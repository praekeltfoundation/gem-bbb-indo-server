
from django import template
from django.shortcuts import reverse
from django.utils.html import format_html

from content.models import Participant, Entry, ParticipantAnswer

register = template.Library()


@register.filter(is_safe=True)
def get_challenge_participants(challenge):
    participants = Participant.objects.filter(user__is_staff=False, challenge=challenge)

    output = '<h1>' + challenge.name + '</h1>'
    output += '<table style="background-repeat:no-repeat; width:100%;margin:0;" border="1">'
    for participant in participants:
        entry = Entry.objects.filter(participant=participant).first()
        participant_answers = ParticipantAnswer.objects.filter(entry=entry)

        output += '<tr>'
        output += '<th>Participant Name</th>'
        output += '<th>Challenge</th>'
        output += '<th>Created On</th>'
        output += '<th>Completed On</th>'
        output += '<th>Read</th>'
        output += '<th>Shortlisted</th>'
        output += '<th>Winner</th>'
        output += '</tr>'

        output += '<tr>'
        output += '<td>' + str(participant.user) + '</td>'
        output += '<td>' + str(challenge.name) + '</td>'
        output += '<td>' + str(challenge.activation_date) + '</td>'
        output += '<td>' + str(participant.date_completed) + '</td>'

        output += '<td>'
        if participant.is_read:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-read' value='{}' checked='checked' />",
                                  'participant-is-read-%d' % participant.id, participant.id)
        else:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-read' value='{}' />",
                                  'participant-is-read-%d' % participant.id, participant.id)
        output += '</td>'

        output += '<td>'
        if participant.is_shortlisted:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-shortlisted' value='{}' checked='checked' />",
                                  'participant-is-shortlisted-%d' % participant.id, participant.id)
        else:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-shortlisted' value='{}' />",
                                  'participant-is-shortlisted-%d' % participant.id, participant.id)
        output += '</td>'

        output += '<td>'
        if participant.is_winner:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-winner' value='{}' checked='checked' />",
                                  'participant-is-winner-%d' % participant.id, participant.id)
        else:
            output += format_html("<input type='checkbox' id='{}' class='mark-is-winner' value='{}' />",
                                  'participant-is-winner-%d' % participant.id, participant.id)
        output += '</td>'
        output += '</tr>'

        output += '<tr>'
        output += '<th>Question</th>'
        output += '<th>Selected Option</th>'
        output += '</tr>'

        for participant_answer in participant_answers:
            output += '<tr>'
            output += '<td>'
            output += str(participant_answer.question)
            output += '</td>'
            output += '<td>'
            output += str(participant_answer.selected_option)
            output += '</td>'
            output += '</tr>'

    output += '</table>'

    return output
