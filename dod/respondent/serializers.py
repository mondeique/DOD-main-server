from rest_framework import serializers, exceptions

from accounts.models import BannedPhoneInfo
from projects.models import Project
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
