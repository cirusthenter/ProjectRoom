from django.db import models
from django.conf import settings
from django.db.models.deletion import CASCADE
from django.utils import timezone
from django.contrib.auth import get_user_model

# Create your models here.


class Room(models.Model):
    name = models.CharField('教室名', max_length=255)
    capacity = models.PositiveIntegerField(
        '最大収容人数', blank=True, null=True, default=0)

    class Meta:
        ordering = ['capacity']

    def __str__(self):
        return self.name


class Unit(models.Model):
    room = models.ForeignKey(Room, verbose_name="教室名",
                             default=None, on_delete=CASCADE)
    weekday = models.IntegerField(
        choices=(
            (0, '月'), (1, '火'), (2, '水'), (3, '木'),
            (4, '金'), (5, '土'), (6, '日')
        )
    )
    period = models.IntegerField(
        choices=(
            (1, '1時限'), (2, '2時限'), (3, '3時限'),
            (4, '4時限'), (5, '5時限')
        )
    )

    class Meta:
        ordering = ['room']

    def __str__(self):
        return str(self.room) + ", " + str(self.period) + " " + str(self.weekday)


class Schedule(models.Model):
    unit = models.ForeignKey(Unit, verbose_name="部屋曜日時限",
                             default=None, on_delete=CASCADE)
    date = models.DateField('日付', default=None)
    faculty = models.CharField(
        '設置学部',
        choices=(
            ('文学部', '文学部'),
            ('経済学部', '経済学部'),
            ('法学部', '法学部'),
            ('商学部', '商学部'),
            ('医学部', '医学部'),
            ('理工学部', '理工学部'),
            ('薬学部', '薬学部'),
            ('その他', 'その他')
        ),
        max_length=10,
    )
    course = models.CharField(
        '科目名', max_length=255,
    )
    subscriber = models.ForeignKey(
        get_user_model(), verbose_name='予約者', on_delete=CASCADE)
    num_students = models.PositiveIntegerField('最大利用者数')

    class Meta:
        ordering = ['date', 'unit']

    def __str__(self):
        date_string = self.date.strftime('%Y/%m/%d')
        return date_string + "-" + str(self.unit.period)


class Log(models.Model):
    user = models.ForeignKey(
        get_user_model(), verbose_name='予約者', on_delete=CASCADE)
    created_at = models.DateTimeField('日時', default=None)
    type = models.CharField(
        'type',
        choices=(
            ('CREATE', 'CREATE'),
            ('UPDATE', 'UPDATE'),
            ('DELETE', 'DELETE'),
        ),
        max_length=6,
    )

    unit = models.ForeignKey(Unit, verbose_name="部屋曜日時限",
                             default=None, on_delete=CASCADE)
    date = models.DateField('日付', default=None)
    faculty = models.CharField(
        '設置学部',
        choices=(
            ('文学部', '文学部'),
            ('経済学部', '経済学部'),
            ('法学部', '法学部'),
            ('商学部', '商学部'),
            ('医学部', '医学部'),
            ('理工学部', '理工学部'),
            ('薬学部', '薬学部'),
            ('その他', 'その他')
        ),
        max_length=10,
    )
    course = models.CharField(
        '科目名', max_length=255,
    )
    num_students = models.PositiveIntegerField('最大利用者数')
