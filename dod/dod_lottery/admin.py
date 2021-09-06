import datetime

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages

from core.sms.utils import MMSV1Manager
from custom_manage.sites import staff_panel
from dod_lottery.models import DODExtraGifticonsItem, DODExtraLotteryLogs
from logic.models import DateTimeLotteryResult, PercentageResult, DODAveragePercentage
from logs.models import MMSSendLog


class DODExtraGifticonsItemStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'price', 'thumbnail_img', 'percentage', 'is_active']

    def thumbnail_img(self, obj):
        if obj.thumbnail:
            return mark_safe('<img src="%s" width=120px "/>' % obj.thumbnail.url)
        return '-'


class CheckUploadedFilter(admin.SimpleListFilter):
    title = 'Uploaded'
    parameter_name = 'uploaded'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(gifticon__isnull=True)

        if self.value() == 'no':
            return queryset.filter(gifticon__isnull=False)


class TodaySendFilter(admin.SimpleListFilter):
    title = 'TodaySend'
    parameter_name = 'today_send'

    def lookups(self, request, model_admin):
        return (
            ('today', 'today'),
        )

    def queryset(self, request, queryset):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        yesterday_filter = datetime.datetime.combine(yesterday, datetime.time(18, 0))  # 어제 저녁 6시
        today_filter = datetime.datetime.combine(today, datetime.time(18, 0))

        if self.value() == 'today':
            # 오늘 보내야 할 당첨자 -> 어제 18:00:01 ~ 오늘 18:00:00
            return queryset.filter(created_at__gte=yesterday_filter, created_at__lte=today_filter)


def send_emails(modeladmin, request, queryset):
    for obj in queryset:
        obj.process()
        messages.error(request, "The message")


send_emails.short_description = 'Send e-mails'


class DODExtraLotteryLogsStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project', 'item_name', 'uploaded', 'phone', 'send', 'created_at', 'send_datetime']
    list_filter = [CheckUploadedFilter, TodaySendFilter]
    actions = ['send_dod_mms']

    def item_name(self, obj):
        if obj.item:
            return obj.item.name
        return '-'

    def uploaded(self, obj):
        if obj.gifticon:
            return mark_safe('<img src="%s" width=120px "/>' % obj.gifticon.url)
        return False

    def send_dod_mms(self, request, queryset):
        for obj in queryset:
            print(obj.gifticon)
            if not obj.gifticon:
                print('asdasd')
                self.message_user(request, "Object {} doesn't have gifticon".format(obj.id), level=messages.ERROR)
                return None
            elif obj.send:
                self.message_user(request, "Object {} already send".format(obj.id), level=messages.ERROR)
                return None

            mms_manager = MMSV1Manager()
            mms_manager.set_content(obj.item.brand, obj.item.name, obj.due_date)
            success, code = mms_manager.send_mms(phone=obj.phone, image_url=obj.gifticon.url)
            if not success:
                MMSSendLog.objects.create(code=code, phone=obj.phone, item_name=obj.item.name, item_url=obj.gifticon.url,
                                          due_date=obj.due_date, brand=obj.item.brand)
                return None
            obj.send = True
            obj.send_datetime = datetime.datetime.now()
            obj.save()

    send_dod_mms.short_description = 'Send DOD lottery MMS'

staff_panel.register(DODExtraGifticonsItem, DODExtraGifticonsItemStaffAdmin)
staff_panel.register(DODExtraLotteryLogs, DODExtraLotteryLogsStaffAdmin)
