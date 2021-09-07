from rest_framework import serializers, exceptions

from accounts.models import BannedPhoneInfo
from dod_lottery.models import DODExtraGifticonsItem
from products.models import Item
from projects.models import Project
from projects.serializers import ProjectProductsGifticonsDetailSerializer
from respondent.models import RespondentPhoneConfirm, Respondent, DeviceMetaInfo, TestRespondent, \
    TestRespondentPhoneConfirm


class SMSRespondentPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField()
    project_key = serializers.CharField()

    def validate(self, attrs):
        super(SMSRespondentPhoneCheckSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        project_key = attrs.get('project_key')
        project = Project.objects.get(project_hash_key=project_key)

        if project.kind == Project.ONBOARDING or not project.status:  # 활성화 안됨 -> 작성자 참여 O & 중복 참여 X
            phone_confirm_queryset = TestRespondentPhoneConfirm.objects.filter(phone=phone).\
                prefetch_related('test_respondent', 'test_respondent__project')
            test_real_phone_confirm_queryset = phone_confirm_queryset.filter(test_respondent__project__project_hash_key=project_key)
            if test_real_phone_confirm_queryset.filter(is_confirmed=True).exists():
                msg = '이미 추첨에 참여하셨어요!'
                raise exceptions.ValidationError(msg)

        elif project.kind == Project.NORMAL and project.status and project.is_active:  # 정상 작동
            phone_confirm_queryset = RespondentPhoneConfirm.objects.filter(phone=phone)\
                .prefetch_related('respondent', 'respondent__project')
            real_phone_confirm_queryset = phone_confirm_queryset.filter(respondent__project__project_hash_key=project_key)
            if BannedPhoneInfo.objects.filter(phone__icontains=phone).exists():
                msg = '어뷰징 응답자입니다. 참여할 수 없습니다.'
                raise exceptions.ValidationError(msg)
            elif real_phone_confirm_queryset.filter(is_confirmed=True).exists():
                msg = '이미 추첨에 참여하셨어요!'
                raise exceptions.ValidationError(msg)
            elif phone == project.owner.phone:
                msg = '추첨생성자는 참여할 수 없습니다.'
                raise exceptions.ValidationError(msg)

        return attrs


class SMSRespondentPhoneConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    confirm_key = serializers.CharField()
    project_key = serializers.CharField()
    validator = serializers.CharField()

    def validate(self, attrs):
        super(SMSRespondentPhoneConfirmSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        confirm_key = attrs.get('confirm_key')
        validator = attrs.get('validator')
        project_key = attrs.get('project_key')
        project = Project.objects.get(project_hash_key=project_key)

        if project.kind in [Project.TEST, Project.ONBOARDING, Project.ANONYMOUS] or not project.status:
            phone_confirm_queryset = TestRespondentPhoneConfirm.objects.filter(phone=phone)
            if not phone_confirm_queryset.filter(confirm_key=confirm_key, is_confirmed=False).exists():
                msg = '잘못된 인증번호 입니다.'
                raise exceptions.ValidationError(msg)

        else:
            phone_confirm_queryset = RespondentPhoneConfirm.objects.filter(phone=phone)\
                .prefetch_related('respondent', 'respondent__project')
            real_phone_confirm_queryset = phone_confirm_queryset.filter(respondent__project__project_hash_key=project_key)
            if BannedPhoneInfo.objects.filter(phone__icontains=phone).exists():
                msg = '어뷰징 응답자입니다. 참여할 수 없습니다.'
                raise exceptions.ValidationError(msg)
            elif real_phone_confirm_queryset.filter(is_confirmed=True).exists():
                msg = '이미 추첨에 참여하셨어요!'  # TODO : send애서 검증
                raise exceptions.ValidationError(msg)
            elif phone == project.owner.phone:
                msg = '추첨생성자는 참여할 수 없습니다.'
                raise exceptions.ValidationError(msg)
            elif not phone_confirm_queryset.filter(confirm_key=confirm_key, is_confirmed=False).exists():
                msg = '잘못된 인증번호 입니다.'
                raise exceptions.ValidationError(msg)

        phone_confirm = phone_confirm_queryset.filter(is_confirmed=False).get(confirm_key=confirm_key)
        phone_confirm.is_confirmed = True
        phone_confirm.save()

        validator = DeviceMetaInfo.objects.get(validator=validator)
        validator.is_confirmed = True
        validator.save()

        return attrs


class RespondentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Respondent
        fields = ['project', 'phone_confirm', 'is_win']


class TestRespondentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestRespondent
        fields = ['project', 'phone_confirm', 'is_win']


class ClientRefererProjectValidateSerializer(serializers.Serializer):
    project_key = serializers.CharField()
    validator = serializers.CharField()


class LotteryAnnouncementRetrieveSerializer(serializers.ModelSerializer):
    left_count = serializers.SerializerMethodField()
    winner_list = serializers.SerializerMethodField()
    total_respondents_count = serializers.SerializerMethodField()
    lottery_type = serializers.SerializerMethodField()
    dod_lottery = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    dod_product_info = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'left_count', 'winner_list', 'total_respondents_count',
                  'lottery_type', 'dod_lottery', 'product_info', 'dod_product_info']

    # def __init__(self, instance=None, *args, **kwargs):
    #     super(LotteryAnnouncementRetrieveSerializer, self).__init__(*args, **kwargs)
    #     self.type = None
    #     print('inin')
        # self.project = instance
        # print(self.project)

        # if self.project.kind == Project.TEST:  # 실시간 추첨 체험(메인)
        #     self.type = 'experience'
        # elif self.project.kind in [Project.ANONYMOUS, Project.ONBOARDING]:  # 테스트링크(온보딩)
        #     self.type = 'test'
        # elif not self.project.status:  # 활성화 안됨
        #     self.type = 'inactive'
        # elif self.project.custom_gifticons.exists():  # 직접 업로드
        #     self.type = 'custom'
        # else:  # 우리쪽 구매
        #     self.type = 'payment'
        # print(self.type)

    def project_type(self):
        if self.project.kind == Project.TEST:  # 실시간 추첨 체험(메인)
            self.type = 'experience'
        elif self.project.kind in [Project.ANONYMOUS, Project.ONBOARDING]:  # 테스트링크(온보딩)
            self.type = 'test'
        elif not self.project.status:  # 활성화 안됨
            self.type = 'inactive'
        elif self.project.custom_gifticons.exists():  # 직접 업로드
            self.type = 'custom'
        else:  # 우리쪽 구매
            self.type = 'payment'
        print(self.type)

    def get_lottery_type(self, project):
        return self.type

    def get_left_count(self, project):
        print('1111')
        self.project = project
        self.project_type()
        if self.type == 'experience':
            return '남은개수 9개(예시)'
        elif self.type == 'test':
            return '남은개수 5개(예시)'
        elif self.type == 'inactive':
            return '남은개수 0개'
        elif self.type == 'custom':
            count = self.project.custom_gifticons.filter(winner_id__isnull=True).count()
            return '남은개수 {}개'.format(count)
        else:
            count = self.project.products.filter(rewards__winner_id__isnull=True).count()
            return '남은개수 {}개'.format(count)

    def get_winner_list(self, project):
        four_digits = []
        if self.type in ['inactive']:
            qs = list(self.project.test_respondents.filter(is_win=True).values_list('phone_confirm__phone', flat=True))
        elif self.type in ['custom', 'payment']:
            qs = list(self.project.respondents.filter(is_win=True).values_list('phone_confirm__phone', flat=True))
        elif self.type == 'test':  # anonymous와 온보딩을 합쳤기 때문에 그냥 지정해서 보여줌
            return ['12*4님', '23*1님', '77*7님']
        else:
            return ['없음']

        for i in qs:
            digits = i[7:]
            crypto_digits = digits[:2]+'*'+digits[-1]
            four_digits.append(crypto_digits)
        return four_digits

    def get_total_respondents_count(self, project):
        if self.type in ['experience', 'test']:  # anonymous와 온보딩을 합쳤기 때문에 그냥 지정해서 보여줌
            return '777명'
        elif self.type == 'inactive':
            count = self.project.test_respondents.all().count()
            return '{}명'.format(count)
        elif self.type in ['custom', 'payment']:
            count = self.project.respondents.all().count()
            return '{}명'.format(count)
        else:
            return '0명'

    def get_dod_lottery(self, project):
        """
        일반적인 추첨(기프티콘 있음)에서 모든 상품이 빠진 경우에만 디오디추첨으로 전환
        """
        if self.type in ['custom']:
            if not self.project.custom_gifticons.filter(winner_id__isnull=True).exists():  # 안 남음
                return True  # dod 추첨
        elif self.type in ['payment']:
            if not self.project.products.filter(rewards__winner_id__isnull=True).exists():  # 안 남음
                return True  # dod 추첨
        return False  # 원래 추첨 방식

    def get_product_info(self, project):
        """
        lottery type 에 맞추어 다르게 return
        """
        if self.type in ['payment']:  # 상품이미지와 남은 개수
            products_distinct_ids = self.project.products.all().values_list('item__id', flat=True).distinct()
            distinct_products = self.project.products.filter(item__id__in=products_distinct_ids)
            empty_dict = {}
            for product in distinct_products:
                empty_dict[product.item.id] = product
            serializer = ProjectProductsGifticonsDetailSerializer(empty_dict.values(), many=True, context={'project': self.project})
            return serializer.data
        elif self.type in ['test', 'experience']:
            data = [{'id': 2,
                     'thumbnail': Item.objects.get(order=998).thumbnail.url,
                     'total_count': 5,
                     'left_count': 3}]
            return data
        elif self.type in ['inactive']:  # 기프티콘 없다는 멘트
            return '기프티콘이 업로드 되지 않았습니다.'
        elif self.type in ['custom']:
            return '설문자가 직접 업로드 한 상품입니다. 랜덤하게 추첨합니다.'
        else:
            return ''

    def get_dod_product_info(self, project):
        qs = DODExtraGifticonsItem.objects.filter(is_active=True)
        serializer = DODExtraGifticonsDetailSerializer(qs, many=True)
        return serializer.data


class DODExtraGifticonsDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = DODExtraGifticonsItem
        fields = ['id', 'name', 'thumbnail', 'percentage']

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return ''

