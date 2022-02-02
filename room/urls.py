from django.urls import path
from . import views

app_name = 'room'

urlpatterns = [
    path('mypage/', views.MyPage.as_view(), name='my_page'),
    path('schedule/<int:pk>/',
         views.MyPageSchedule.as_view(), name='schedule'),
    path('schedule/<int:pk>/delete/',
         views.MyPageScheduleDelete.as_view(), name='schedule_delete'),
    path('user/<int:pk>/', views.UserPage.as_view(), name='user_page'),
    path('user/', views.Users.as_view(), name='users'),
    path('calendar/', views.Calendar.as_view(), name="calendar"),
    path('calendar/<int:month>/<int:day>/',
         views.Calendar.as_view(), name='calendar'),
    path('day/<int:month>/<int:day>/',
         views.ScheduleInDay.as_view(), name='day'),
    path('booking/<int:pk>/<int:month>/<int:day>/',
         views.Booking.as_view(), name='booking'),
    path('room/<int:month>/<int:day>/<int:period>',
         views.RoomsInUnit.as_view(), name='room')
]
