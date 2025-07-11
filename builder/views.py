from django.template import RequestContext

from django.conf import settings

URL_PREFIX = settings.URL_PREFIX

def builder_render(request, *args, **kwargs):
    """ Append an attribute onto the response so that we can grab the context
    from it in the track decorator. It has to be an attribute so that it
    doesn't depend on the function returning the response to be decorated by
    @trackGrade to get proper output. """

    from django.shortcuts import render

    response = render(request, *args, **kwargs)
    response.context = args[1]

    return response

def builder_main(request):
    """ This is the main view presented to users after login.
        Instructors will be shown a link to view grades and student progress,
        students will be shown their current progress in all of the games
        that they have records in.
    """

    template = 'builder.html'
    c = {}
    return builder_render(request,
                          template,
                          c,
                          context_instance=RequestContext(request))

