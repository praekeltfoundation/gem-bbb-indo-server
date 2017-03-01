
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse, HttpResponse
from wagtail.contrib.modeladmin.views import IndexView

from .models import Participant


def participant_list_view(request):
    context = {
        'participants': Participant.objects.all()
    }

    return render(request, 'content/admin/participant/list.html', context)


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_read(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_read = not participant.is_read
    participant.save()
    return JsonResponse({})


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_shortlisted(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_shortlisted = not participant.is_shortlisted
    participant.save()
    return JsonResponse({})


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_winner(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_winner = not participant.is_winner
    participant.save()
    return JsonResponse({})

from .reports import GoalReport


class GoalAdminIndex(IndexView):
    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'EXPORT':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment;filename=export.csv'
            GoalReport.export_csv(response)
            return response

    def get_template_names(self):
        return 'admin/goal/index.html'