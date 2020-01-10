#!/usr/bin/env python

# encoding: utf-8

'''

@author: JOJ

@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.

@contact: zhouguanjie@qq.com

@software: JOJ

@file: stark.py

@time: 2019-12-12 15:09

@desc:

'''

from stark.service.stark import site, ModelStark
from .models import *

site.register(School)


class ClassConfig(ModelStark):
    def display_classname(self, obj=None, header=False):
        if header:
            return "班级名称"
        class_name = "%s(%s)" % (obj.course.name, str(obj.semester))

        return class_name

    list_display = [display_classname, "tutor", "teachers"]


site.register(ClassList, ClassConfig)


class UserConfig(ModelStark):
    list_display = ["name", "email", "depart"]


site.register(UserInfo, UserConfig)

from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse, redirect, render


class CustomerConfig(ModelStark):
    def display_gender(self, obj=None, header=False):
        if header:
            return "性别"
        # 选择框字段获取解释的方式
        return obj.get_gender_display()

    def display_course(self, obj=None, header=False):
        if header:
            return "咨询课程"
        temp = []
        for course in obj.course.all():
            s = "<a href='/stark/crm/customer/cancel_course/%s/%s' style='border:1px solid #369;padding:3px 6px'><span>%s</span></a>&nbsp;" % (
                obj.pk, course.pk, course.name,)

            temp.append(s)
        print(temp)
        return mark_safe("".join(temp))

    list_display = ["name", display_gender, display_course, "course", "consultant"]

    def cancel_course(self, request, customer_id, course_id):
        print(customer_id, course_id)
        obj = Customer.objects.filter(pk=customer_id).first()
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self, request):
        pass

    def extra_url(self):
        temp = []
        temp.append(url(r"cancel_course/(\d+)/(\d+)", self.cancel_course))
        return temp


site.register(Customer, CustomerConfig)

site.register(Department)
site.register(Course)
site.register(ConsultRecord)


class CourseRecordConfig(ModelStark):

    def score(self, request, course_record_id):
        if request.method == "POST":
            print(request.POST)

            data = {}
            for key, value in request.POST.items():
                if key == "csrfmiddlewaretoken": continue
                field, pk = key.rsplit('_', 1)
                if pk in data:
                    data[pk][field] = value
                else:
                    data[pk] = {field: value}  # data  {4:{"score":90}}
            print("data", data)
            for pk, update_data in data.items():
                StudyRecord.objects.filter(pk=pk).update(**update_data)

            return redirect(request.path)
        else:
            study_record_list = StudyRecord.objects.filter(course_record=course_record_id)
            score_choices = StudyRecord.score_choices

            return render(request, "score.html", locals())

    def extra_url(self):
        temp = []
        temp.append(url(r"record_score/(\d+)", self.score))
        return temp

    def record_score(self, obj=None, header=False):
        if header:
            return "录入成绩"
        return mark_safe("<a href='record_score/%s'>录入成绩</a>" % obj.pk)

    def record(self, obj=None, header=False):
        if header:
            return "考勤"
        return mark_safe("<a href='/stark/crm/studyrecord/?course_record=%s'>记录</a>" % obj.pk)

    list_display = ['class_obj', "day_num", "teacher", record, record_score]

    def patch_studyrecord(self, request, queryset):

        temp = []
        for course_record in queryset:
            #         与course_record关联的班级对应的所有的学生
            student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            for student in student_list:
                obj = StudyRecord(student=student, course_record=course_record)
                temp.append(obj)

            StudyRecord.objects.bulk_create(temp)

    patch_studyrecord.short_description = "批量生成学习记录"
    actions = [patch_studyrecord, ]


site.register(CourseRecord, CourseRecordConfig)


class StudyConfig(ModelStark):
    list_display = ["student", "course_record", "record", "score"]

    def patch_late(self, requst, queryset):
        queryset.update(record="late")

    patch_late.short_description = "迟到"
    actions = [patch_late]


site.register(StudyRecord, StudyConfig)

from django.http import JsonResponse


class studentConfig(ModelStark):
    def score_view(self, request, sid):

        if request.is_ajax():
            print(request.GET)
            sid = request.GET.get("sid")
            cid = request.GET.get("cid")
            study_record_list = StudyRecord.objects.filter(student=sid, course_record__class_obj=cid)
            data_list = []
            for study_record in study_record_list:
                day_num = study_record.course_record.day_num
                data_list.append(["day%s" % day_num, study_record.score])
            print(data_list)
            return JsonResponse(data_list, safe=False)
        else:
            student = Student.objects.filter(pk=sid).first()
            class_list = student.class_list.all()
            return render(request, "score_view.html", locals())

    def extra_url(self):
        temp = []
        temp.append(url(r"score_view/(\d+)", self.score_view))
        return temp

    def score_show(self, obj=None, header=False):
        if header:
            return "查看成绩"
        return mark_safe("<a href='/stark/crm/student/score_view/%s'>查看成绩</a>" % obj.pk)

    list_display = ["customer", "class_list", score_show]
    list_display_links = ["customer"]


site.register(Student, studentConfig)
