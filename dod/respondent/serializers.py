from rest_framework import serializers, exceptions

from respondent.models import RespondentPhoneConfirm, Respondent


class SMSRespondentPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField()


class SMSRespondentPhoneConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    confirm_key = serializers.CharField()
    project_key = serializers.CharField()

    def validate(self, attrs):
        super(SMSRespondentPhoneConfirmSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        confirm_key = attrs.get('confirm_key')
        phone_confirm = RespondentPhoneConfirm.objects.filter(phone=phone, is_confirmed=False)
        if not phone_confirm.exists():
            msg = '다시한번 인증번호를 요청해 주세요'
            raise exceptions.ValidationError(msg)
        if RespondentPhoneConfirm.objects.filter(phone=phone, is_confirmed=True, confirm_key=confirm_key).exists():
            msg = '이미 사용된 인증번호입니다.'
            raise exceptions.ValidationError(msg)
        elif not phone_confirm.filter(confirm_key=confirm_key).exists():
            msg = '잘못된 인증번호 입니다.'
            raise exceptions.ValidationError(msg)

        phone_confirm = phone_confirm.get(confirm_key=confirm_key)
        phone_confirm.is_confirmed = True
        phone_confirm.save()

        return attrs


class RespondentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Respondent
        fields = ['project', 'phone_confirm', 'is_win']
