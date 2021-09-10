import json
import random
import string

import requests
from django.db import transaction, OperationalError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
import datetime
import time
# Create your views here.
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from accounts.models import PhoneConfirm, User
from accounts.serializers import SMSSignupPhoneCheckSerializer, SMSSignupPhoneConfirmSerializer
from core.sms.utils import SMSV2Manager, MMSV1Manager
from core.tools import get_client_ip
from django.conf import settings

from dod_lottery.models import DODExtraGifticonsItem, DODExtraLotteryLogs
from logic.models import DateTimeLotteryResult, PercentageResult, DODAveragePercentage
from logs.models import MMSSendLog
from projects.models import Project
from products.models import Product, Reward, Item
from respondent.models import RespondentPhoneConfirm, Respondent, TestRespondentPhoneConfirm, AlertAgreeRespondent
from respondent.serializers import SMSRespondentPhoneCheckSerializer, RespondentCreateSerializer, \
    SMSRespondentPhoneConfirmSerializer, TestRespondentCreateSerializer
def generate_random_key(length=10):
    return ''.join(random.choices(string.digits + string.ascii_letters, k=length))


class SMSViewSet(viewsets.GenericViewSet):
    """
    sms 전송시 공통으로 사용하는 viewset
    """
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'send':
            serializer = SMSSignupPhoneCheckSerializer
        elif self.action == 'confirm':
            serializer = SMSSignupPhoneConfirmSerializer
        elif self.action == 'respondent_send':
            serializer = SMSRespondentPhoneCheckSerializer
        elif self.action == 'respondent_confirm':
            serializer = SMSRespondentPhoneConfirmSerializer
        else:
            serializer = super(SMSViewSet, self).get_serializer_class()
        return serializer

    @action(methods=['post'], detail=False)
    def send(self, request, *args, **kwargs):
        """
        회원가입시 인증번호 발송하는 api입니다.
        api: api/v1/sms/send
        method: POST
        data: {'phone'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data['phone']
            sms_manager = SMSV2Manager()
            sms_manager.set_content()
            sms_manager.create_instance(phone=phone, kinds=PhoneConfirm.SIGN_UP)

            if not sms_manager.send_sms(phone=phone):
                return Response("Failed send sms", status=status.HTTP_410_GONE)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def confirm(self, request, *args, **kwargs):
        """
        회원가입시 인증번호 인증 api입니다. 인증시 다음페이지(비밀번호설정)에서 사용할 phone을 리턴합니다.
        api: api/v1/sms/confirm
        method: POST
        data: {'phone', 'confirm_key'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid(raise_exception=True):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'phone': serializer.validated_data['phone']}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def respondent_send(self, request, *args, **kwargs):
        """
        설문자 인증번호 발송시 사용하는 핸드폰인증입니다.
        api: api/v1/sms/respondent_send/
        method: POST
        data: {'phone', 'project_key'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data['phone']
            sms_manager = SMSV2Manager()
            sms_manager.set_respondent_content()
            project = Project.objects.filter(project_hash_key=data.get('project_key')).last()
            sms_manager.create_respondent_send_instance(phone=phone, project=project)

            if not sms_manager.send_sms(phone=phone):
                return Response("Failed send sms", status=status.HTTP_410_GONE)
            if AlertAgreeRespondent.objects.filter(phone=phone).exists():
                agreed = True
            else:
                agreed = False
            return Response({"agreed": agreed}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @action(methods=['post'], detail=False)
    def respondent_confirm(self, request, *args, **kwargs):
        """
        설문자 인증번호 인증 api입니다. 인증시 서버에서 5-10초후 reward MMS를 발송합니다.
        api: api/v1/sms/respondent_confirm
        method: POST
        전화번호, 인증번호 와 url에서 파싱한 project_key와 validator를 담아서 보내주어야 합니다.
        data: {'phone', 'confirm_key', 'project_key', 'validator', "agree"}
        """
        data = request.data
        agree = data.get('agree')
        if agree:
            AlertAgreeRespondent.objects.create(phone=data.get('phone'),
                                                key=generate_random_key(10),
                                                agree=True)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid(raise_exception=True):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not Project.objects.filter(project_hash_key=data.get('project_key')).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.data = serializer.validated_data
        self._set_project()

        # UPDATED 20210907 dod_lottery False
        self.dod_lottery = False

        if self.project.kind in [Project.TEST, Project.ONBOARDING, Project.ANONYMOUS] or not self.project.status:

            self._create_test_respondent()
            won_thumbnail = Item.objects.get(order=999).won_thumbnail.url

            return Response({'id': self.project.id,
                             'is_win': True,
                             'dod_lottery': self.dod_lottery,
                             'won_thumbnail': won_thumbnail  # UPDATED 20210725 당첨이미지
                             }, status=status.HTTP_200_OK)

        self._create_respondent()
        item_name = ''
        won_thumbnail = ''
        if self.is_win:
            if self.project.custom_gifticons.exists():
                # UPDATED 20210725 직접 업로드
                self._set_custom_gifticon()
                phone = self.data.get('phone')
                item_url = self.gifticon.gifticon_img.url
                item_name = '직접 업로드'

                if type(item_url) is tuple:
                    item_url = ''.join(item_url)

                mms_manager = MMSV1Manager()
                mms_manager.set_custom_upload_content()
                success, code = mms_manager.send_mms(phone=phone, image_url=item_url)
                if not success:
                    MMSSendLog.objects.create(code=code, phone=phone, item_name=item_name, item_url=item_url)

                self.gifticon.winner_id = self.respondent.id
                self.gifticon.save()
                won_thumbnail = self.gifticon.item.won_thumbnail.url

            else:
                # UPDATED 20210725 구매
                self._set_random_reward()

                phone = self.data.get('phone')
                brand = self.reward.product.item.brand.name
                item_name = self.reward.product.item.name
                item_url = self.reward.reward_img.url
                due_date = self.reward.due_date

                if type(item_url) is tuple:
                    item_url = ''.join(item_url)

                if type(item_name) is tuple:
                    item_name = ''.join(item_name)

                mms_manager = MMSV1Manager()
                mms_manager.set_content(brand, item_name, due_date)
                success, code = mms_manager.send_mms(phone=phone, image_url=item_url)
                if not success:
                    MMSSendLog.objects.create(code=code, phone=phone, item_name=item_name, item_url=item_url,
                                              due_date=due_date, brand=brand)

                self.reward.winner_id = self.respondent.id
                self.reward.save()
                item_name = self.reward.product.item.short_name
                won_thumbnail = self.reward.product.item.won_thumbnail.url

        # UPDATED 20210907 dod lottery
        elif self.dod_lottery:
            if self._am_i_dod_winner():
                dod_prizes = DODExtraGifticonsItem.objects.filter(is_active=True)
                dod_prizes_ids = list(dod_prizes.values_list('pk', flat=True))
                dod_prizes_percentage = list(dod_prizes.values_list('percentage', flat=True))
                dod_reward_id = random.choices(dod_prizes_ids, weights=dod_prizes_percentage)[0]
                dod_reward = dod_prizes.get(id=dod_reward_id)

                DODExtraLotteryLogs.objects.create(item=dod_reward,
                                                   project=self.project,
                                                   phone=self.data.get('phone')
                                                   )
                self.is_win = True
                won_thumbnail = dod_reward.thumbnail.url

        return Response({'id': self.project.id,
                         'is_win': self.is_win,
                         # 'item_name': item_name,  # WILL BE DEPRECATED
                         'dod_lottery': self.dod_lottery,  # 디오디 추첨으로 당첨되었다를 공지하기 위해
                         'won_thumbnail': won_thumbnail  # UPDATED 20210725 당첨이미지
                         }, status=status.HTTP_200_OK)

    def _set_custom_gifticon(self):
        custom_gifticons = self.project.custom_gifticons.filter(winner_id__isnull=True)
        self.gifticon = random.choices(custom_gifticons)[0]

    def _set_random_reward(self): # TODO: 에러날경우 패스 혹은 문의하기로
        reward_queryset = Reward.objects.filter(winner_id__isnull=True) \
            .select_related('product', 'product__item', 'product__project', 'product__item__brand')
        remain_rewards = reward_queryset.filter(product__project=self.project)
        remain_rewards_id = list(remain_rewards.values_list('id', flat=True))
        remain_rewards_price = list(remain_rewards.values_list('product__item__price', flat=True))
        reward_weight = list(map(lambda x: round(1 / x * (sum(remain_rewards_price) / len(remain_rewards_price)))
                            , remain_rewards_price))
        random_reward_id_by_weight = random.choices(remain_rewards_id, weights=reward_weight)[0]
        self.reward = reward_queryset.get(id=random_reward_id_by_weight)

    def _set_project(self):
        project_queryset = Project.objects.filter(project_hash_key=self.data.get('project_key'))\
            .prefetch_related('respondents', 'respondents__phone_confirm', 'custom_gifticons')

        self.project = project_queryset.get(project_hash_key=self.data.get('project_key'))
        if self.project.kind in [Project.TEST, Project.ONBOARDING] or not self.project.status:
            self.phone_confirm = TestRespondentPhoneConfirm.objects.filter(phone=self.data.get('phone'),
                                                                           confirm_key=self.data.get('confirm_key'),
                                                                           is_confirmed=True).last()
        else:
            self.phone_confirm = RespondentPhoneConfirm.objects.filter(phone=self.data.get('phone'),
                                                                       confirm_key=self.data.get('confirm_key'),
                                                                       is_confirmed=True).last()

    def _create_respondent(self):
        self.is_win = self._am_i_winner()
        data = {'project': self.project.id,
                'phone_confirm': self.phone_confirm.id,
                'is_win': self.is_win}

        serializer = RespondentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.respondent = serializer.save()

    def _create_test_respondent(self):
        data = {'project': self.project.id,
                'phone_confirm': self.phone_confirm.id,
                'is_win': True}

        serializer = TestRespondentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.respondent = serializer.save()

    def _am_i_winner(self):
        # 프로젝트 생성자는 무조건 꽝!
        if self.phone_confirm.phone == self.project.owner.phone:
            return False

        if self.project.select_logics.last().kind == 1:
            # BEFORE v2 update

            if self.project.products.filter(rewards__isnull=True).exists():
                # staff 업로드 하지 않았다면 꽝
                return False

            self.lucky_times = self.project.select_logics.last().lottery_times.filter(is_used=False)
            now = datetime.datetime.now()
            self.valid_lucky_times = self.lucky_times.filter(lucky_time__lte=now)
            if not self.valid_lucky_times.exists():
                # 당첨 안된 경우
                return False
            else:
                try:
                    with transaction.atomic(using='default'):
                        vlt = DateTimeLotteryResult.objects.select_for_update(nowait=True)\
                            .filter(logic__project=self.project).filter(is_used=False, lucky_time__lte=now).first()
                        vlt.is_used = True
                        vlt.save()
                        val = True
                except OperationalError:
                    val = False
                except DateTimeLotteryResult.DoesNotExist:
                    val = False
                return val

        elif self.project.select_logics.last().kind == 3:
            # UPDATED v2 : percentage
            self.left_percentages = self.project.select_logics.last().percentages.filter(is_used=False)
            if not self.left_percentages.exists():
                # 추첨 다 됨
                # UPDATED 20210907 dod lottery
                self.dod_lottery = True
                return False
            else:
                percentage = self.left_percentages.first().percentage  # 당첨확률 : ex: 2.1
                ex_percentage = abs(100 - percentage)
                result = random.choices([True, False], weights=[percentage, ex_percentage])  # ex: True 일 확률 2.1
                if not result[0]:
                    return False
                else:
                    try:
                        # 만약 동시에 호출하여 연속 접속자가 당첨인 경우, db lock걸어 중복 전송 방지
                        with transaction.atomic(using='default'):
                            vlt = PercentageResult.objects.select_for_update(nowait=True) \
                                .filter(logic__project=self.project).filter(is_used=False).first()
                            vlt.is_used = True
                            vlt.save()
                            val = True
                    except OperationalError:
                        val = False
                    except PercentageResult.DoesNotExist:
                        val = False
                    return val

    def _am_i_dod_winner(self):
        # 15% 확률로 들어옴
        probability_of_entry = DODAveragePercentage.objects.last().average_percentage  # 15.0
        ex_percentage = abs(100 - probability_of_entry)
        result = random.choices([True, False], weights=[probability_of_entry, ex_percentage])
        return result


class SendMMSAPIView(APIView):
    """
    당첨자 3초 후 문자전송을 위해 만듬 (20210622)

    [DEPRECATED] 발송실패가 많음. (20210625)
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        ip = get_client_ip(request)
        if ip not in settings.ALLOWED_HOSTS:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        phone = data.get('phone')
        brand = data.get('brand')
        item_name = data.get('item_name')
        item_url = data.get('item_url')
        due_date = data.get('due_date')
        time.sleep(3)  # wait 3 seconds
        mms_manager = MMSV1Manager()
        mms_manager.set_content(brand, item_name, due_date)
        success, code = mms_manager.send_mms(phone=phone, image_url=item_url)
        if not success:
            MMSSendLog.objects.create(code=code, phone=phone, item_name=item_name, item_url=item_url, due_date=due_date)
        # MMSSendLog.objects.create(code=code, phone=phone, item_name=item_name, item_url=item_url, due_date=due_date)
        return Response(status=status.HTTP_200_OK)

