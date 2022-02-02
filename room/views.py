from django import shortcuts
from django.contrib import messages
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
import datetime
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.contrib.auth.models import User
from django.urls import reverse
from urllib.parse import urlencode

# Create your views here.
from django.views import generic
from .models import Room, Unit, Schedule, Log

THIS_YEAR = 2021

ADMIN = [
    "admin1@keio.jp",
    "admin2@keio.jp",
]


def is_available(booking_date):
    PUBLIC_BOOKING_START = datetime.date(year=THIS_YEAR, month=6, day=3)
    PUBLIC_BOOKING_END = datetime.date(year=THIS_YEAR, month=7, day=10)
    LIMITED_BOOKING_PERIOD_START = datetime.date(
        year=THIS_YEAR, month=6, day=21)
    LIMITED_BOOKING_PERIOD_END = datetime.date(
        year=THIS_YEAR, month=6, day=26)

    today = datetime.date.today()
    if booking_date > PUBLIC_BOOKING_END:
        return False
    if booking_date < LIMITED_BOOKING_PERIOD_START:
        return False
    # if booking_date <= today:
    #     return False
    if today >= PUBLIC_BOOKING_START:
        return True
    return LIMITED_BOOKING_PERIOD_START <= booking_date <= LIMITED_BOOKING_PERIOD_END


class Base(generic.TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_anonymous:
            context['is_admin'] = False
        else:
            context['is_admin'] = self.request.user.email in ADMIN
        return context


class Calendar(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()

        # どの日を基準にカレンダーを表示するかの処理。
        # 年月日の指定があればそれを、なければ今日からの表示。
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if month and day:
            base_date = datetime.date(year=THIS_YEAR, month=month, day=day)
        else:
            base_date = today

        # カレンダーは1週間分表示するので、基準日から1週間の日付を作成しておく
        days = [base_date + datetime.timedelta(days=day) for day in range(7)]
        start_day = days[0]
        end_day = days[-1]

        # 1限から5限まで、1週間分の、予約可能数をカウントする辞書を作る
        calendar = {}
        for period in range(1, 6):
            row = {}
            for day in days:
                row[day] = [0, 0, not is_available(day)]
            calendar[period] = row

        # 各曜日の各時限の空いている教室の数
        num_slots = [[0] * 6 for _ in range(7)]

        # 各曜日で予約可能スロットの数をカウント
        unit_rooms = Unit.objects.filter()
        for unit in unit_rooms:
            num_slots[unit.weekday][unit.period] += 1

        for period in range(1, 6):
            for day in days:
                calendar[period][day][0] = num_slots[day.weekday()][period]

        # カレンダー表示する最初と最後の日の間にある予約を取得する
        for schedule in Schedule.objects.filter(date__gte=start_day, date__lte=end_day):
            booking_period = schedule.unit.period
            booking_date = schedule.date
            if booking_period in calendar and booking_date in calendar[booking_period]:
                calendar[booking_period][booking_date][0] -= 1
                calendar[booking_period][booking_date][1] += 1

        for period in calendar:
            for day in calendar[period]:
                if day <= today:
                    calendar[period][day][0] = 0
                if (not is_available(day)):
                    calendar[period][day][0] = 0

        context['is_admin'] = self.request.user.email in ADMIN
        context['calendar'] = calendar
        context['days'] = days
        context['start_day'] = start_day
        context['end_day'] = end_day
        context['before'] = days[0] - datetime.timedelta(days=7)
        context['next'] = days[-1] + datetime.timedelta(days=1)
        context['today'] = today
        return context


class ScheduleInDay(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/day.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        date = datetime.date(year=THIS_YEAR, month=month, day=day)
        schedules = Schedule.objects.filter(date=date)
        units = Unit.objects.filter(weekday=date.weekday())
        rooms = Room.objects.filter()
        rooms_dict = dict()
        today = datetime.date.today()
        for room in rooms:
            rooms_dict[room] = [None for _ in range(5)]
        schedules_dict = dict()
        for schedule in schedules:
            schedules_dict[schedule.unit] = schedule
        for unit in units:
            if unit in schedules_dict:
                rooms_dict[unit.room][unit.period - 1] = schedules_dict[unit]
            else:
                rooms_dict[unit.room][unit.period - 1] = unit
        context['rooms'] = rooms_dict
        context['schedules'] = schedules_dict
        context['schedules_set'] = set(schedules)
        context['date'] = date
        context['today'] = datetime.date.today()
        context['is_admin'] = self.request.user.email in ADMIN
        context['is_available'] = is_available(date)
        if date <= today:
            context['is_available'] = False
        return context


class RoomsInUnit(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/unit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        date = datetime.date(year=THIS_YEAR, month=month, day=day)
        weekday = date.weekday()
        today = datetime.date.today()
        period = self.kwargs.get('period')
        unit_set = set()
        if (is_available(date)):
            unit_set = set(Unit.objects.filter(weekday=weekday, period=period))
        schedules = []
        schedules_in_day = Schedule.objects.filter(date=date)
        for schedule in schedules_in_day:
            if schedule.unit in unit_set:
                schedules.append(schedule)
                unit_set.remove(schedule.unit)
        is_admin = self.request.user.email in ADMIN
        if date <= today and not is_admin:
            raise Http404
        if not is_available(date) and not is_admin:
            raise Http404
        context['is_admin'] = is_admin
        context['month'] = month
        context['day'] = day
        context['date'] = date
        context['today'] = today
        context['period'] = period
        context['units'] = list(unit_set)
        context['schedules'] = schedules
        return context


class Booking(LoginRequiredMixin, generic.CreateView):
    model = Schedule
    fields = ('course', 'faculty', 'num_students')
    template_name = 'room/booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = get_object_or_404(Unit, pk=self.kwargs['pk'])
        context['unit'] = unit
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        context['month'] = month
        context['day'] = day
        date = datetime.date(year=THIS_YEAR, month=month, day=day)
        context['date'] = date
        context['can_book'] = True
        context['message'] = ""
        today = datetime.date.today()
        context['is_admin'] = self.request.user.email in ADMIN
        if date.weekday() != unit.weekday:
            raise Http404
        elif date <= today:
            raise Http404
        elif not is_available(date):
            raise Http404
        elif Schedule.objects.filter(unit=unit, date=date).exists():
            context['can_book'] = False
            context['message'] = "すでに予約されています"
            context['schedule'] = Schedule.objects.filter(
                unit=unit, date=date)[0]
        elif len(Schedule.objects.filter(subscriber=self.request.user)) >= 2:
            context['can_book'] = False
            context['message'] = "予約数が上限に達しているため登録できません"
        return context

    def form_valid(self, form):
        unit = get_object_or_404(Unit, pk=self.kwargs['pk'])
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        date = datetime.date(year=THIS_YEAR, month=month, day=day)
        today = datetime.date.today()
        if date.weekday() != unit.weekday:
            messages.error(self.request, '不正な日時です。')
        elif Schedule.objects.filter(unit=unit, date=date).exists():
            messages.error(self.request, '入れ違いで予約がありました')
        elif date <= today:
            messages.error(self.request, "予約可能期間を過ぎました")
        elif len(Schedule.objects.filter(subscriber=self.request.user)) >= 2:
            messages.error(self.request, "予約数が上限に達しているため登録できません")
        elif form.cleaned_data.get("num_students") > unit.room.capacity:
            messages.error(self.request, "利用者数が収容人数を越えているため予約できません")
            url = reverse('room:booking', kwargs={
                "pk": unit.id, "month": month, "day": day})
            print(url)
            return redirect(url)
        else:
            log = Log()
            log.user = self.request.user
            log.created_at = datetime.datetime.now()
            log.type = "CREATE"
            log.unit = unit
            log.date = date
            log.faculty = form.cleaned_data.get("faculty")
            log.course = form.cleaned_data.get("course")
            log.num_students = form.cleaned_data.get("num_students")
            log.save()
            schedule = form.save(commit=False)
            schedule.unit = unit
            schedule.date = date
            schedule.subscriber = self.request.user
            schedule.save()
            message = date.strftime('%Y/%m/%d') + "の" + \
                str(unit.period) + "限に" + str(unit.room) + "教室を予約しました"
            messages.success(self.request, message)
        return redirect('room:my_page')


class MyPage(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/my_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        context['schedule_list'] = Schedule.objects.filter(
            subscriber=self.request.user, date__gte=today)
        context['past_schedule_list'] = Schedule.objects.filter(
            subscriber=self.request.user, date__lt=today)
        context['log_list'] = Log.objects.filter(
            user=self.request.user)
        context['is_admin'] = self.request.user.email in ADMIN
        return context


class MyPageSchedule(LoginRequiredMixin, generic.UpdateView):
    model = Schedule
    fields = ('course', 'faculty', 'num_students')

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse('room:schedule', kwargs={"pk": pk})

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])

        if form.cleaned_data.get("num_students") > schedule.unit.room.capacity:
            messages.error(self.request, "利用者数が収容人数を越えているため予約できません")
        elif self.request.user != schedule.subscriber:
            messages.error(self.request, "他者の予約は編集できません")
        else:
            schedule = form.save(commit=False)
            log = Log()
            log.user = self.request.user
            log.created_at = datetime.datetime.now()
            log.type = "UPDATE"
            log.unit = schedule.unit
            log.date = schedule.date
            log.faculty = schedule.faculty
            log.course = schedule.course
            log.num_students = schedule.num_students
            log.save()
            schedule.save()
            message = log.date.strftime('%Y/%m/%d') + "の" + \
                str(log.unit.period) + "限" + \
                str(log.unit.room) + "教室の予約を更新しました"
            messages.success(self.request, message)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        context['schedule'] = schedule
        context['faculty'] = schedule.faculty
        context['unit'] = schedule.unit
        context['num_students'] = schedule.num_students
        date = schedule.date
        context['month'] = date.month
        context['day'] = date.day
        context['date'] = date
        context['email'] = self.request.user.email
        is_admin = self.request.user.email in ADMIN
        context['is_admin'] = is_admin
        context['can_edit'] = True
        today = datetime.date.today()
        if date <= today:
            context['can_edit'] = False
        if schedule.subscriber != self.request.user and not is_admin:
            raise Http404
        return context


class MyPageScheduleDelete(LoginRequiredMixin, generic.DeleteView):
    model = Schedule

    def get_success_url(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        log = Log()
        log.user = self.request.user
        log.created_at = datetime.datetime.now()
        log.type = "DELETE"
        log.unit = schedule.unit
        log.date = schedule.date
        log.faculty = schedule.faculty
        log.course = schedule.course
        log.num_students = schedule.num_students
        log.save()
        message = log.date.strftime('%Y/%m/%d') + "の" + \
            str(log.unit.period) + "限" + str(log.unit.room) + "教室の予約を削除しました"
        messages.success(self.request, message)
        return reverse('room:my_page')

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(MyPageScheduleDelete, self).get_object()
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        date = schedule.date
        today = datetime.date.today()
        if date <= today:
            raise Http404
        if schedule.subscriber != self.request.user:
            raise Http404
        return obj


class UserPage(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/user_page.html'

    def get_context_data(self, **kwargs):
        if self.request.user.email not in ADMIN:
            raise Http404
        user_id = self.kwargs['pk']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        context['schedule_list'] = Schedule.objects.filter(
            subscriber=user, date__gte=today)
        context['past_schedule_list'] = Schedule.objects.filter(
            subscriber=user, date__lt=today)
        context['log_list'] = Log.objects.filter(
            user=user)
        context['theuser'] = user
        context['num_logs'] = len(context['log_list'])
        context['is_admin'] = self.request.user.email in ADMIN
        return context


class Users(LoginRequiredMixin, generic.TemplateView):
    template_name = 'room/users.html'

    def get_context_data(self, **kwargs):
        if self.request.user.email not in ADMIN:
            raise Http404
        users = User.objects.filter()
        context = super().get_context_data(**kwargs)
        users_dict = dict()
        for user in users:
            users_dict[user] = [user, 0, 0, 0]  # [user, 直近の予約件数, 過去の予約件数, ログ数]
        today = datetime.date.today()
        schedules = Schedule.objects.filter(
            date__gte=today)
        for schedule in schedules:
            users_dict[schedule.subscriber][1] += 1
        past_schedules = Schedule.objects.filter(
            date__lt=today)
        for past_schedule in past_schedules:
            users_dict[past_schedule.subscriber][2] += 1
        logs = Log.objects.filter()
        for log in logs:
            users_dict[log.user][3] += 1
        users = list(users_dict.values())
        users.sort(key=lambda x: x[3], reverse=True)
        context['users'] = users
        context['num_users'] = len(users)
        context['num_schedules'] = len(schedules)
        context['num_past_schedules'] = len(past_schedules)
        context['num_logs'] = len(logs)
        context['is_admin'] = self.request.user.email in ADMIN
        return context
