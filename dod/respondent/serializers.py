from rest_framework import serializers, exceptions

from projects.models import Project
from respondent.models import RespondentPhoneConfirm, Respondent, DeviceMetaInfo, TestRespondent, \
    TestRespondentPhoneConfirm


class SMSRespondentPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField()


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

        if project.kind == Project.TEST:
            phone_confirm_queryset = TestRespondentPhoneConfirm.objects.filter(phone=phone)
            if not phone_confirm_queryset.filter(confirm_key=confirm_key, is_confirmed=False).exists():
                msg = '잘못된 인증번호 입니다.'
                raise exceptions.ValidationError(msg)

        else:
            phone_confirm_queryset = RespondentPhoneConfirm.objects.filter(phone=phone)\
                .prefetch_related('respondent', 'respondent__project')
            real_phone_confirm_queryset = phone_confirm_queryset.filter(respondent__project__project_hash_key=project_key)
            if real_phone_confirm_queryset.filter(is_confirmed=True).exists():
                msg = '이미 추첨에 참여하셨어요!'
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
