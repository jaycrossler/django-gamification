# -*- coding: utf-8 -*-

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, as long as
# any reuse or further development of the software attributes the
# National Geospatial-Intelligence Agency (NGA) authorship as follows:
# 'This software (django-gamification)
# is provided to the public as a courtesy of the National
# Geospatial-Intelligence Agency.
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from django.contrib.auth.models import User
from django.views.generic import ListView
from django.db.models import Sum
from django.http import HttpResponseRedirect
from models import Project, Points
from gamification.badges.models import ProjectBadge, ProjectBadgeToUser
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
import json
from gamification.badges.utils import project_badge_count
from gamification.core.utils import badge_count,top_n_badge_winners,user_project_badge_count
from gamification.core.models import Project
from gamification.core.forms import AwardForm


class PointsListView(ListView):

    paginate_by = 15
    model = Points

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Points.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        cv = super(PointsListView, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['username'])
        cv['profile'] = badge_count(user)
        return cv

class MasterProjectListView(ListView):

    paginate_by = 15
    model = Project

    def get_queryset(self):
        return Project.objects.all()

    def get_context_data(self, **kwargs):
        cv = super(MasterProjectListView, self).get_context_data(**kwargs)
        cv['profile'] = top_n_badge_winners(cv['object_list'],5)
        return cv

class UserProjectPointsView(ListView):
    paginate_by = 15
    model = User

    def get_queryset(self):
        return User.objects.filter(username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        cv = super(UserProjectPointsView, self).get_context_data(**kwargs)
        project = get_object_or_404(Project, name=self.kwargs['projectname'])
        user = cv['object_list'][0]

        cv['username'] = user.username
        cv['projectbadges'] = user_project_badge_count(user,project)
        cv['projectname'] = project.description
        return cv

class ProjectListView(ListView):

    paginate_by = 15
    model = Project

    def get_queryset(self):
        return Project.objects.filter(name=self.kwargs['projectname'])

    def get_context_data(self, **kwargs):
        cv = super(ProjectListView, self).get_context_data(**kwargs)
        cv['profile'] = top_n_badge_winners(cv['object_list'],5)
        return cv

class BadgeListView(ListView):

    model = ProjectBadge

    def get_queryset(self):
        project = get_object_or_404(Project, name=self.kwargs['projectname'])
        return ProjectBadge.objects.filter(project=project).values('name','description','awardLevel','multipleAwards','badge__icon')

    def get_context_data(self, **kwargs):
        cv = super(BadgeListView, self).get_context_data(**kwargs)
        cv['project_name'] = self.kwargs['projectname']
        return cv

class UserView(ListView):

    model = User

    def get_queryset(self):
        return User.objects.all().order_by('last_name')

    def get_context_data(self, **kwargs):
        cv = super(UserView, self).get_context_data(**kwargs)
        return cv


def award(request, *args, **kwargs):
    if request.method == 'POST':
        form = AwardForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, username=kwargs['username'])
            projectbadge = ProjectBadge.objects.get(pk=request.POST['award_id'])
            points = Points(user=user,projectbadge=projectbadge,value=request.POST['points'],description=request.POST['comment'])
            points.save()
            return HttpResponseRedirect('/users/%s/projects/%s' % (kwargs['username'], kwargs['projectname']))

    else:
        form = AwardForm()

    return render(request, 'core/award.html', { 'form': form, })

# REST interface

def projects(request, *args, **kwargs):
    if request.method == 'GET':
        try:
            user = get_object_or_404(User,username=kwargs['username'])
            project = get_object_or_404(Project,name=kwargs['projectname'])
        except Http404, e:
            context = { 'message' : e.__str__().split()[1] + ' not found' }
            return HttpResponse(json.dumps(context),'application/json',404)

        projbadges = ProjectBadge.objects.filter(project=project)
        badge_info = project_badge_count(user,project,projbadges)
        badge_detail_list = []
        for bi in badge_info:
            bstr = '{ "name":"%s", "awarded":%d, "url":"%s"}' % \
               ( bi['projectbadge__name'], bi['count'], bi['projectbadge__badge__icon'])
            badge_detail_list.append(json.loads(bstr))

        resp = '{"username":"%s", "badges":%s}' % (user.username, json.dumps(badge_detail_list))
        return HttpResponse(resp, mimetype="application/json")
    elif request.method == 'PUT':
        point_args = {}
        if request.GET.__contains__('comment'):
            point_args['description'] = request.GET['comment']

        if request.GET.__contains__('points'):
            point_args['value'] = int(request.GET['points'])
        else:
            context = {'message' : 'No points included in request'}
            return HttpResponse(json.dumps(context), 'application/json', 400)

        try:
            point_args['user'] = get_object_or_404(User,username=kwargs['username'])
            project = get_object_or_404(Project,name=kwargs['projectname'])
        except Http404, e:
            context = { 'message' : e.__str__().split()[1] + ' not found' }
            return HttpResponse(json.dumps(context),'application/json',404)
            
        award = request.GET['award']

        try:
            point_args['projectbadge'] = get_object_or_404(ProjectBadge,name=award)
        except Http404, e:
            context = { 'message' : 'Project not found' }
            return HttpResponse(json.dumps(context), 'application/json', 404)

        # award points
        points = Points(**point_args)
        points.save()

        return HttpResponseRedirect('/users/%s/projects/%s' % (point_args['user'], project))
       