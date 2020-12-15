from django.db import models
from django.contrib.humanize.templatetags.humanize import ordinal
from django.conf import settings
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.html import mark_safe

from api.exceptions import ModelAccessException, ModelNotExistException
from api.models.utils import EngageManager
from api.models.calliope import Parameter, Run_Parameter, \
    Abstract_Tech, Abstract_Tech_Param
from taskmeta.models import CeleryTask

import uuid
import pandas as pd
import numpy as np
import re
import os
import json
from copy import deepcopy


class Model(models.Model):
    class Meta:
        db_table = "model"
        verbose_name_plural = "[0] Models"
        ordering = ['name', '-snapshot_version']
    objects = EngageManager()
    objects_all = models.Manager()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    snapshot_version = models.IntegerField(blank=True, null=True)
    snapshot_base = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True)
    public = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        if self.snapshot_version:
            return '%s [v%s]' % (self.name, self.snapshot_version)
        else:
            return '%s' % (self.name)

    def handle_edit_access(self, user):
        """ Requires Model Edit Permissions: 1
        Used to verify a user's full access to a model """
        permissions = self.get_user_permissions(user)
        if permissions in [1]:
            return True
        raise ModelAccessException("NO ACCESS")

    def handle_view_access(self, user):
        """ Requires Model Access Permissions: 0 or 1
        Used to verify a user's view access to a model """
        permissions = self.get_user_permissions(user)
        if permissions in [0, 1]:
            return bool(permissions)
        raise ModelAccessException("NO ACCESS")

    def get_user_permissions(self, user):
        """ Lookup the permissions that the user has on the given model
        -1: No Access, 0: View Only, 1: Can Edit """

        if self.public:
            return 0
        if user.is_authenticated is False:
            return -1
        # If snapshot, retrieve the base model
        if self.snapshot_base is not None:
            model = self.snapshot_base
            is_snapshot = True
        else:
            model = self
            is_snapshot = False
        # Retrieve permissions
        models = Model_User.objects.filter(user=user, model=model)
        if len(models) > 0:
            if is_snapshot:
                return 0
            else:
                return int(models.first().can_edit)
        else:
            return -1

    def notify_collaborators(self, user):
        """ Update the notification badges displayed to the other collaborators
        on a model """
        model_users = Model_User.objects.filter(model=self).exclude(user=user)
        for model_user in model_users:
            model_user.notifications += 1
            model_user.save()

    @classmethod
    def by_uuid(cls, model_uuid):
        """ Get a requested model by its UUID """
        model = cls.objects.filter(uuid=model_uuid).first()
        if not model:
            raise ModelNotExistException("Model is None.")
        return model

    def get_uuid(self):
        """ Get the string formatted UUID of the given model """
        return str(self.uuid)

    @property
    def locations(self):
        """ Get all configured location objects """
        return self.location_set.all()

    @property
    def technologies(self):
        """ Get all configured technology objects """
        return self.technology_set.all()

    @property
    def loc_techs(self):
        """ Get all configured loc_tech objects """
        return self.loc_tech_set.all()

    @property
    def scenarios(self):
        """ Get all configured scenario objects """
        return self.scenario_set.all()

    @property
    def scenario_loc_techs(self):
        """ Get all configured scenario_loc_techs objects """
        return self.scenario_loc_tech_set.all()

    @property
    def runs(self):
        """ Get all configured run objects """
        return self.run_set.all()

    @property
    def carriers(self):
        """ Get all configured carrier strings """
        CARRIER_IDS = [4, 5, 6, 23, 66, 67, 68, 69, 70, 71]
        carriers = Tech_Param.objects.filter(
            model=self,
            parameter_id__in=CARRIER_IDS)
        carriers = carriers.values_list('value', flat=True)
        carriers_list = []
        for carrier in carriers:
            carriers_list += carrier.split(',')
        return list(set(carriers_list))

    @property
    def favorites(self):
        """ Get all configured favorited parameter ids """
        return list(Model_Favorite.objects.filter(
            model=self).values_list('parameter_id', flat=True))

    def collaborators(self):
        """ Get all model_user objects (collaborators) """
        return Model_User.objects.filter(model=self)

    def deprecate_runs(self, location_id=None,
                       technology_id=None, scenario_id=None):
        """ When a user has made changes to the model configurations, deprecate
        previous runs to inform all collaborators of these changes """
        if location_id or technology_id:
            if location_id:
                loc_techs = self.loc_techs.filter(
                    Q(location_1_id=location_id) | Q(location_2_id=location_id))
            if technology_id:
                loc_techs = self.loc_techs.filter(technology_id=technology_id)
            scenario_loc_techs = self.scenario_loc_techs.filter(loc_tech__in=loc_techs)
            # Scenario IDs to Update
            scenario_ids = scenario_loc_techs.values_list('scenario_id', flat=True)
        elif scenario_id:
            # Scenario IDs to Update
            scenario_ids = [scenario_id]
        else:
            scenario_ids = []

        self.runs.filter(scenario_id__in=scenario_ids).update(deprecated=True)
        return True

    def duplicate(self, is_snapshot):
        """ Duplicate the given model as either a new editable model or
        a new view-only snapshot. """
        return DuplicateModelManager(self, is_snapshot).run()


class Model_User(models.Model):
    class Meta:
        db_table = "model_user"
        verbose_name_plural = "[0] Model Users"
        ordering = ['user__user_profile__organization']
    objects = EngageManager()
    objects_all = models.Manager()

    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    last_access = models.DateTimeField(auto_now=True, null=True)
    notifications = models.IntegerField(default=0)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s - %s' % (self.model, self.user)

    @classmethod
    def update(cls, model, user, can_edit):
        """ Update the access permissions of a model collaborator """
        existing_collaborator = cls.objects.filter(
            user=user, model=model)
        if existing_collaborator:
            could_edit = existing_collaborator.first().can_edit
            if can_edit is None:
                existing_collaborator.hard_delete()
                message = 'Collaborator removed.'
            elif can_edit != could_edit:
                existing_collaborator.update(can_edit=can_edit)
                message = 'Updated collaborator.'
            else:
                message = 'Already a collaborator.'
        else:
            if can_edit is None:
                message = 'Not a collaborator.'
            else:
                cls.objects.create(user=user,
                                   model=model,
                                   can_edit=can_edit)
                message = 'Added collaborator.'
        return message


class Model_Comment(models.Model):
    class Meta:
        db_table = "model_comment"
        verbose_name_plural = "[0] Model Comments"
        ordering = ['-created']
    objects = EngageManager()
    objects_all = models.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    type = models.CharField(max_length=200, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.comment)

    def safe_comment(self):
        """ Mark the stored comment as safe for html rendering """
        return mark_safe(self.comment)

    def icon(self):
        """ Get the appropriate icon for the given comment type """
        if self.type == 'add':
            return mark_safe('<i class="fas fa-plus"></i>')
        elif self.type == 'edit':
            return mark_safe('<i class="far fa-edit"></i>')
        elif self.type == 'delete':
            return mark_safe('<i class="fas fa-trash"></i>')
        elif self.type == 'comment':
            return mark_safe('<i class="fas fa-comment"></i>')
        elif self.type == 'version':
            return mark_safe('<i class="far fa-clock"></i>')
        else:
            return ''


class Model_Favorite(models.Model):
    class Meta:
        db_table = "model_favorite"
        verbose_name_plural = "[0] Model Favorites"
    objects = EngageManager()
    objects_all = models.Manager()

    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s - %s' % (self.model, self.parameter)


class User_File(models.Model):
    class Meta:
        db_table = "user_file"
        verbose_name_plural = "[0] User File Uploads"
        ordering = ['-created']
    objects = EngageManager()
    objects_all = models.Manager()

    filename = models.FileField(upload_to='user_files/')
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.filename)

    def simple_filename(self):
        """ Get the filename without its full path """
        return str(self.filename).split('/')[-1]


class DuplicateModelManager():
    """ Class to duplicate a model as either snapshot or copy """

    IGNORED_PARENTS = ['model', 'user', 'parameter', 'run_parameter',
                       'abstract_tech', 'abstract_tech_param',
                       'upload_task', 'build_task', 'run_task']

    IGNORED_CHILDREN = ['model', 'model_user']

    def __init__(self, model, is_snapshot):

        self.model = model
        self.is_snapshot = is_snapshot
        self._change_dict = {}
        self._table_set = []
        self._children = []
        for field in self.model._meta.get_fields():
            if field.one_to_many:
                self._change_dict[field.name] = {}
                self._table_set += list(
                    getattr(self.model, '{}_set'.format(field.name)).all())

    def run(self):
        """ Master method for performing a model duplication and returning
        the new model instance """

        self._create_model()
        self._create_children()
        self._update_foreign_keys()

        return self.new_model

    def _create_model(self):
        """ Create the new model as snapshot or copy """

        new_model = deepcopy(self.model)

        new_model.pk = None
        new_model.uuid = str(uuid.uuid4())
        new_model.public = False
        if self.is_snapshot:
            latest = Model.objects.filter(name=self.model.name).exclude(
                snapshot_version=None).values_list('snapshot_version',
                                                   flat=True)
            new_model.snapshot_version = np.max(list(latest) + [0]) + 1
            new_model.snapshot_base = self.model
        else:
            new_model.snapshot_version = None
            new_model.snapshot_base = None
        new_model.save()
        self.new_model = new_model

    def _create_children(self):
        """ Duplicate the children records for the new model """

        for obj in self._table_set:

            # Initiate the copy
            key = obj._meta.label_lower.split('.')[1]
            if key in self.IGNORED_CHILDREN:
                continue
            old_pk = obj.pk
            obj.pk = None
            obj.model_id = self.new_model.id

            # Create copy; save created date if exists
            if hasattr(obj, 'created'):
                created = obj.created
            obj.save()

            # Restore created date if exists
            if hasattr(obj, 'created'):
                obj.created = created
                obj.save()

            # Record the old and new primary keys
            new_pk = obj.pk
            self._change_dict[key][old_pk] = new_pk

            # Record the parent foreign keys
            if 'parents' not in self._change_dict[key]:
                parents = []
                for field in obj._meta.get_fields():
                    if (field.many_to_one is True):
                        if (field.name not in self.IGNORED_PARENTS):
                            parents.append(field.name)

                self._change_dict[key]['parents'] = parents

            if len(self._change_dict[key]['parents']) > 0:
                self._children.append(obj)

    def _update_foreign_keys(self):
        """ Update the new model's children with new foreign keys """

        for obj in self._children:
            key = obj._meta.label_lower.split('.')[1]
            parents = self._change_dict[key]['parents']
            for parent in parents:
                old_id = getattr(obj, '{}_id'.format(parent))
                if old_id:

                    if parent in ['location_1', 'location_2']:
                        new_id = self._change_dict['location'][old_id]
                    else:
                        new_id = self._change_dict[parent][old_id]
                    setattr(obj, '{}_id'.format(parent), new_id)
            obj.save()


class Timeseries_Meta(models.Model):
    class Meta:
        db_table = "timeseries_meta"
        verbose_name_plural = "[3] Timeseries Meta"
        ordering = ['-is_uploading', '-created']
    objects = EngageManager()
    objects_all = models.Manager()

    name = models.CharField(max_length=200)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    file_uuid = models.UUIDField(default=uuid.uuid4)
    is_uploading = models.BooleanField(default=False)
    failure = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=200, null=True, blank=True)
    original_timestamp_col = models.IntegerField(null=True)
    original_value_col = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    upload_task = models.ForeignKey(
        to=CeleryTask,
        to_field="id",
        related_name="timeseries_meta",
        null=True,
        on_delete=models.PROTECT,
        default=None
    )

    def __str__(self):
        if self.original_filename is None:
            return self.name
        else:
            s = "%s - %s (%s column)" % (self.name,
                                         self.original_filename,
                                         ordinal(1 + self.original_value_col))
            return s

    def get_period(self):
        """ Calculate the min/max dates of the given timeseries """
        if None in [self.start_date, self.end_date]:
            timeseries = self.get_timeseries()
            self.start_date = timeseries.datetime.min()
            self.end_date = timeseries.datetime.max()
            self.save()
        return (self.start_date.replace(tzinfo=None),
                self.end_date.replace(tzinfo=None))

    def get_timeseries(self):
        """ Retrieve the data from the given timeseries """
        directory = '{}/timeseries'.format(settings.DATA_STORAGE)
        input_fname = '{}/{}.csv'.format(directory, self.file_uuid)
        timeseries = pd.read_csv(input_fname, parse_dates=[0])
        timeseries.index = pd.to_datetime(timeseries.datetime)
        return timeseries

    @classmethod
    def create_ts_8760(cls, model, name, values):
        """ Creates an hourly (8760) timeseries for a full year
        Using arbitrary year of 2019, and has no other significance """

        # TODO: year as argument
        start_date = "2019-01-01 00:00"
        end_date = "2019-12-31 23:00"

        dates = list(pd.date_range(start_date, end_date, freq="1h"))
        timeseries = pd.DataFrame(np.array([dates, values]).T,
                                  columns=['time', 'value'])
        timeseries = timeseries.set_index('time')
        timeseries.index.name = 'datetime'

        meta = cls.objects.create(model=model, name=name,
                                  start_date=start_date, end_date=end_date)
        try:
            directory = "{}/timeseries".format(settings.DATA_STORAGE)
            os.makedirs(directory, exist_ok=True)
            fname = "{}/{}.csv".format(directory, meta.file_uuid)
            timeseries.to_csv(fname)
            return True

        except Exception:
            meta.delete()
            return False


class Technology(models.Model):
    class Meta:
        db_table = "technology"
        verbose_name_plural = "[2] Technologies"
        ordering = ['pretty_name']
    objects = EngageManager()
    objects_all = models.Manager()

    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    tag = models.CharField(max_length=200, blank=True, null=True)
    pretty_tag = models.CharField(max_length=200, blank=True, null=True)
    is_linear = models.BooleanField(null=True, default=True)
    is_expansion = models.BooleanField(null=True, default=True)
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)

    @property
    def calliope_name(self):
        """ Get the calliope appropriate name for the given technology """
        if self.tag:
            return '{}-{}'.format(self.name, self.tag)
        else:
            return '{}'.format(self.name)

    @property
    def color(self):
        """ Lookup the color from the technology's parameters """
        p = Tech_Param.objects.filter(technology=self,
                                      parameter__name='color').first()
        return p.value if p else "white"

    @property
    def carrier_in(self):
        """ Lookup the input carrier from the technology's parameters """
        c_ins = ['carrier', 'carrier_in', 'carrier_in_2', 'carrier_in_3']
        p = Tech_Param.objects.filter(technology=self,
                                      parameter__name__in=c_ins
                                      ).order_by('value')
        return ','.join(list(p.values_list('value', flat=True)))

    @property
    def carrier_out(self):
        """ Lookup the output carrier from the technology's parameters """
        c_outs = ['carrier', 'carrier_out', 'carrier_out_2', 'carrier_out_3']
        p = Tech_Param.objects.filter(technology=self,
                                      parameter__name__in=c_outs
                                      ).order_by('value')
        return ','.join(list(p.values_list('value', flat=True)))

    def to_dict(self):
        d = {'model': self.__class__.__name__}
        d.update(model_to_dict(self))
        return d

    def to_json(self):
        d = self.to_dict()
        j = json.dumps(d)
        return j

    def get_color(self):
        """ Lookup the color from the technology's parameters """
        color = Tech_Param.objects.filter(technology=self,
                                          parameter_id=3).first()
        if color:
            return color.value
        else:
            return "#fff"

    def duplicate(self, model_id, pretty_name):
        """ Duplicate and return a new technology instance """
        new_tech = deepcopy(self)
        new_tech.pk = None
        new_tech.pretty_name = pretty_name
        new_tech.name = ParamsManager.simplify_name(pretty_name)
        new_tech.model_id = model_id
        new_tech.save()
        tech_params = Tech_Param.objects.filter(technology=self)
        # Handle New & Existing Timeseries Meta
        tmetas = {}
        existing_tmetas = {}
        for t in Timeseries_Meta.objects.filter(model_id=model_id):
            existing_tmetas[t.name] = t
        # Iterate copy over Technology's parameters
        for tech_param in tech_params:
            tech_param.pk = None
            tech_param.technology_id = new_tech.id
            tech_param.model_id = model_id
            tmeta = deepcopy(tech_param.timeseries_meta)
            if tmeta is not None:
                original_pk = tmeta.pk
                if tmeta.name in existing_tmetas.keys():
                    # Timeseries already exists (by name)
                    tech_param.timeseries_meta = existing_tmetas[tmeta.name]
                    tech_param.value = existing_tmetas[tmeta.name].pk
                elif original_pk in tmetas.keys():
                    # Timeseries was just copied in a previous iteration
                    tech_param.timeseries_meta = tmetas[original_pk]
                    tech_param.value = tmetas[original_pk].pk
                else:
                    # Creating a new timeseries meta record
                    tmeta.pk = None
                    tmeta.model_id = model_id
                    tmeta.save()
                    tech_param.timeseries_meta = tmeta
                    tech_param.value = tmeta.pk
                    tmetas[original_pk] = tmeta
            tech_param.save()
        return new_tech

    def update(self, form_data):
        """ Update the Technology parameters stored in Tech_Param """
        if 'is_linear' in form_data.keys():
            self.is_linear = bool(int(form_data['is_linear']))
            self.save()
        if 'is_expansion' in form_data.keys():
            self.is_expansion = bool(int(form_data['is_expansion']))
            self.save()
        METHODS = ['essentials', 'add', 'edit', 'delete']
        for method in METHODS:
            if method in form_data.keys():
                data = form_data[method]
                getattr(Tech_Param, '_' + method)(self, data)


class Tech_Param(models.Model):
    class Meta:
        db_table = "tech_param"
        verbose_name_plural = "[2] Technology Parameters"
    objects = EngageManager()
    objects_all = models.Manager()

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, blank=True, null=True)
    raw_value = models.CharField(max_length=200, blank=True, null=True)
    timeseries = models.BooleanField(default=False)
    timeseries_meta = models.ForeignKey(Timeseries_Meta,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    @property
    def placeholder(self):
        """ Value to place in the HTML placeholder field """
        return self.raw_value or self.value

    @classmethod
    def _essentials(cls, technology, data):
        """ Update a technologies essential parameters """
        for key, value in data.items():
            if key == 'tech_name':
                if value:
                    technology.name = ParamsManager.simplify_name(value)
                    technology.pretty_name = value
            elif key == 'tech_tag':
                technology.tag = ParamsManager.simplify_name(value)
                technology.pretty_tag = value
            elif key == 'tech_description':
                technology.description = value
            elif key == 'cplus_carrier':
                cls._cplus_carriers(technology, value, data['cplus_ratio'])
            elif key == 'cplus_ratio':
                continue
            else:
                cls.objects.filter(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key).hard_delete()
                if value:
                    cls.objects.create(
                        model_id=technology.model_id,
                        technology_id=technology.id,
                        parameter_id=key,
                        value=value.replace(',', ''))
            technology.save()

        if technology.pretty_tag:
            tech_full_name = '{} ({})'.format(technology.pretty_name,
                                              technology.pretty_tag)
        else:
            tech_full_name = technology.pretty_name
        tech_full_name_record = cls.objects.filter(
            model_id=technology.model_id,
            technology_id=technology.id,
            parameter_id=2)
        if len(tech_full_name_record) == 0:
            cls.objects.create(
                model_id=technology.model_id,
                technology_id=technology.id,
                parameter_id=2,
                value=tech_full_name)
        else:
            tech_full_name_record.update(value=tech_full_name)

    @classmethod
    def _cplus_carriers(cls, technology, carriers, ratios):
        """ Update a technologies (Conversion Plus) carrier parameters """
        RATIOS_ID = 7
        ratios_dict = {}
        for param_id in carriers.keys():
            # Delete Old Parameter
            cls.objects.filter(
                model_id=technology.model_id,
                technology_id=technology.id,
                parameter_id__in=[param_id, RATIOS_ID]).hard_delete()
            # Create New Parameter
            val = ','.join([v for v in carriers[param_id] if v != ''])
            if val:
                cls.objects.create(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=param_id,
                    value=val)
                name = Parameter.objects.get(id=param_id).name
                # Update Ratios Dict
                if name not in ratios_dict:
                    ratios_dict[name] = {}
                for carrier, ratio in zip(carriers[param_id],
                                          ratios[param_id]):
                    try:
                        ratio_val = float(ratio) if float(ratio) >= 0 else 1
                    except ValueError:
                        ratio_val = 1
                    if carrier:
                        ratios_dict[name][carrier] = ratio_val
        # Update Ratios Parameter
        ratios_val = json.dumps(ratios_dict)
        cls.objects.create(
            model_id=technology.model_id,
            technology_id=technology.id,
            parameter_id=RATIOS_ID,
            value=ratios_val)

    @classmethod
    def _add(cls, technology, data):
        """ Add a new parameter to a technology """
        for key, value_dict in data.items():
            if (('year' in value_dict) & ('value' in value_dict)):
                years = value_dict['year']
                values = value_dict['value']
                num_records = np.min([len(years), len(values)])
                new_objects = []
                for i in range(num_records):
                    vals = str(values[i]).split('||')
                    new_objects.append(cls(
                        model_id=technology.model_id,
                        technology_id=technology.id,
                        year=years[i],
                        parameter_id=key,
                        value=vals[0],
                        raw_value=vals[1] if len(vals) > 1 else vals[0]))
                cls.objects.bulk_create(new_objects)

    @classmethod
    def _edit(cls, technology, data):
        """ Edit a technology's parameters """
        if 'parameter' in data:
            for key, value in data['parameter'].items():
                vals = str(value).split('||')
                cls.objects.filter(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key).hard_delete()
                cls.objects.create(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key,
                    value=vals[0],
                    raw_value=vals[1] if len(vals) > 1 else vals[0])
        if 'timeseries' in data:
            for key, value in data['timeseries'].items():
                cls.objects.filter(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key).hard_delete()
                cls.objects.create(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key,
                    value=value,
                    timeseries_meta_id=value,
                    timeseries=True)
        if 'parameter_instance' in data:
            instance_items = data['parameter_instance'].items()
            for key, value_dict in instance_items:
                parameter_instance = cls.objects.filter(
                    model_id=technology.model_id,
                    id=key)
                if 'value' in value_dict:
                    vals = str(value_dict['value']).split('||')
                    parameter_instance.update(
                        value=vals[0],
                        raw_value=vals[1] if len(vals) > 1 else vals[0])
                if 'year' in value_dict:
                    parameter_instance.update(year=value_dict['year'])

    @classmethod
    def _delete(cls, technology, data):
        """ Delete a technology's parameters """
        if 'parameter' in data:
            for key, value in data['parameter'].items():
                cls.objects.filter(
                    model_id=technology.model_id,
                    technology_id=technology.id,
                    parameter_id=key).hard_delete()
        elif 'parameter_instance' in data:
            instance_items = data['parameter_instance'].items()
            for key, value in instance_items:
                cls.objects.filter(
                    model_id=technology.model_id,
                    id=key).hard_delete()


class Location(models.Model):
    class Meta:
        db_table = "location"
        verbose_name_plural = "[1] Locations"
        ordering = ['pretty_name']
    objects = EngageManager()
    objects_all = models.Manager()

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    available_area = models.FloatField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)


class Loc_Tech(models.Model):
    class Meta:
        db_table = "loc_tech"
        verbose_name_plural = "[3] Location Technologies"
        ordering = ['technology__abstract_tech__name',
                    'technology__pretty_name',
                    'location_1', 'location_2']
    objects = EngageManager()
    objects_all = models.Manager()

    location_1 = models.ForeignKey(Location,
                                   on_delete=models.CASCADE,
                                   related_name="location_1")
    location_2 = models.ForeignKey(Location,
                                   on_delete=models.CASCADE,
                                   related_name="location_2",
                                   blank=True, null=True)
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        if self.location_2:
            return '%s <-> %s | %s [%s]' % (self.location_1, self.location_2,
                                            self.technology,
                                            self.technology.pretty_tag)
        else:
            return '%s | %s [%s]' % (self.location_1, self.technology,
                                     self.technology.pretty_tag)

    def update(self, form_data):
        """ Update the Location Technology parameters
        stored in Loc_Tech_Param """
        METHODS = ['add', 'edit', 'delete']
        for method in METHODS:
            if method in form_data.keys():
                data = form_data[method]
                getattr(Loc_Tech_Param, '_' + method)(self, data)
        # Remove system-wide parameters
        sw = Loc_Tech_Param.objects.filter(parameter__is_systemwide=True)
        sw.hard_delete()


class Loc_Tech_Param(models.Model):
    class Meta:
        db_table = "loc_tech_param"
        verbose_name_plural = "[3] Location Technology Parameters"
    objects = EngageManager()
    objects_all = models.Manager()

    loc_tech = models.ForeignKey(Loc_Tech, on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, blank=True, null=True)
    raw_value = models.CharField(max_length=200, blank=True, null=True)
    timeseries = models.BooleanField(default=False)
    timeseries_meta = models.ForeignKey(Timeseries_Meta,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    @property
    def placeholder(self):
        """ Value to place in the HTML placeholder field """
        return self.raw_value if self.raw_value else self.value

    @classmethod
    def _add(cls, loc_tech, data):
        """ Add a new parameter to a location technology """
        for key, value_dict in data.items():
            if (('year' in value_dict) & ('value' in value_dict)):
                years = value_dict['year']
                values = value_dict['value']
                num_records = np.min([len(years), len(values)])
                new_objects = []
                for i in range(num_records):
                    vals = str(values[i]).split('||')
                    new_objects.append(cls(
                        model_id=loc_tech.model_id,
                        loc_tech_id=loc_tech.id,
                        year=years[i],
                        parameter_id=key,
                        value=vals[0],
                        raw_value=vals[1] if len(vals) > 1 else vals[0]))
                cls.objects.bulk_create(new_objects)

    @classmethod
    def _edit(cls, loc_tech, data):
        """ Edit a location technology parameter """
        if 'parameter' in data:
            for key, value in data['parameter'].items():
                vals = str(value).split('||')
                cls.objects.filter(
                    model_id=loc_tech.model_id,
                    loc_tech_id=loc_tech.id,
                    parameter_id=key).hard_delete()
                cls.objects.create(
                    model_id=loc_tech.model_id,
                    loc_tech_id=loc_tech.id,
                    parameter_id=key,
                    value=vals[0],
                    raw_value=vals[1] if len(vals) > 1 else vals[0])
        if 'timeseries' in data:
            for key, value in data['timeseries'].items():
                cls.objects.filter(
                    model_id=loc_tech.model_id,
                    loc_tech_id=loc_tech.id,
                    parameter_id=key).hard_delete()
                cls.objects.create(
                    model_id=loc_tech.model_id,
                    loc_tech_id=loc_tech.id,
                    parameter_id=key,
                    value=value,
                    timeseries_meta_id=value,
                    timeseries=True)
        if 'parameter_instance' in data:
            instance_items = data['parameter_instance'].items()
            for key, value_dict in instance_items:
                parameter_instance = cls.objects.filter(
                    model_id=loc_tech.model_id,
                    id=key)
                if 'value' in value_dict:
                    vals = str(value_dict['value']).split('||')
                    parameter_instance.update(
                        value=vals[0],
                        raw_value=vals[1] if len(vals) > 1 else vals[0])
                if 'year' in value_dict:
                    parameter_instance.update(year=value_dict['year'])

    @classmethod
    def _delete(cls, loc_tech, data):
        """ Delete a location technology parameter """
        if 'parameter' in data:
            for key, value in data['parameter'].items():
                cls.objects.filter(
                    model_id=loc_tech.model_id,
                    loc_tech_id=loc_tech.id,
                    parameter_id=key).hard_delete()
        elif 'parameter_instance' in data:
            instance_items = data['parameter_instance'].items()
            for key, value in instance_items:
                cls.objects.filter(
                    model_id=loc_tech.model_id,
                    id=key).hard_delete()


class Scenario(models.Model):
    class Meta:
        db_table = "scenario"
        verbose_name_plural = "[4] Scenarios"
        ordering = ['name']
    objects = EngageManager()
    objects_all = models.Manager()

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.name)

    def duplicate(self, name):
        """ Duplicate and return a new scenario with a copy of the original's
        configuration and settings instances """
        # Create Scenario
        new_scenario = deepcopy(self)
        new_scenario.pk = None
        new_scenario.name = name
        new_scenario.save()
        # Copy Parameters
        scenario_params = Scenario_Param.objects.filter(scenario=self)
        for scenario_param in scenario_params:
            scenario_param.pk = None
            if scenario_param.run_parameter.name == "name":
                scenario_param.value = "{}: {}".format(new_scenario.model.name,
                                                       name)
            scenario_param.scenario_id = new_scenario.id
            scenario_param.save()
        # Copy Configuration
        scenario_loc_techs = Scenario_Loc_Tech.objects.filter(scenario=self)
        for scenario_loc_tech in scenario_loc_techs:
            scenario_loc_tech.pk = None
            scenario_loc_tech.scenario_id = new_scenario.id
            scenario_loc_tech.save()
        return new_scenario

    def timeseries_precheck(self):
        """
        Extracts timeseries data to verify and validate before a new run
        """
        scenario_loc_techs = Scenario_Loc_Tech.objects.filter(scenario=self)
        ts_params = {}
        missing_ts = []
        t_format = "%m/%d/%Y, %H:%M:%S"
        for scenario_loc_tech in scenario_loc_techs:
            loc_tech = scenario_loc_tech.loc_tech
            technology = loc_tech.technology
            t_params = Tech_Param.objects.filter(technology=technology,
                                                 timeseries=True)
            lt_params = Loc_Tech_Param.objects.filter(loc_tech=loc_tech,
                                                      timeseries=True)

            param_sets = [(t_params, 'technologies', technology),
                          (lt_params, 'loc_techs', loc_tech)]
            for param_set in param_sets:
                for param in param_set[0]:
                    if param.timeseries_meta:
                        period = param.timeseries_meta.get_period()
                        key = (str(loc_tech), str(param.parameter))
                        ts_params[key] = [t.strftime(t_format) for t in period]
                    else:
                        if param_set[1] == 'loc_techs':
                            loc_tech_id = loc_tech.id
                        else:
                            loc_tech_id = ''
                        missing_ts.append((param_set[1], technology.id,
                                           loc_tech_id, str(param_set[2]),
                                           str(param.parameter)))
        ts_params = [list(k) + list(v) for k, v in ts_params.items()]
        return json.dumps(ts_params), set(missing_ts)


class Scenario_Loc_Tech(models.Model):
    class Meta:
        db_table = "scenario_loc_tech"
        verbose_name_plural = "[4] Scenario Location Technologies"
        ordering = ['loc_tech__technology__name']
    objects = EngageManager()
    objects_all = models.Manager()

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    loc_tech = models.ForeignKey(Loc_Tech, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.loc_tech)


class Scenario_Param(models.Model):
    class Meta:
        db_table = "scenario_param"
        verbose_name_plural = "[4] Scenario Parameters"
        ordering = ['run_parameter__pretty_name', 'year', 'id']
    objects = EngageManager()
    objects_all = models.Manager()

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    run_parameter = models.ForeignKey(Run_Parameter, on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    value = models.CharField(max_length=200)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    @classmethod
    def update(cls, scenario, form_data):
        """ Update the Scenario parameters stored in Scenario_Param """
        METHODS = ['add', 'edit', 'delete']
        for method in METHODS:
            if method in form_data.keys():
                data = form_data[method]
                getattr(cls, '_' + method)(scenario, data)

    @classmethod
    def _add(cls, scenario, data):
        """ Add a new parameter to a scenario """
        for p_id in data:
            years = data[p_id]['years']
            values = data[p_id]['values']
            new_objects = []
            for i in range(len(years)):
                if values[i] != '':
                    new_objects.append(cls(
                        run_parameter_id=p_id,
                        model_id=scenario.model_id,
                        scenario_id=scenario.id,
                        year=cls.int_or_zero(years[i]),
                        value=values[i]))
            cls.objects.bulk_create(new_objects)

    @classmethod
    def _edit(cls, scenario, data):
        """ Edit a scenario parameter """
        if 'year' in data.keys():
            for key, val in data['year'].items():
                param = cls.objects.filter(
                    model_id=scenario.model_id,
                    scenario_id=scenario.id,
                    id=key)
                param.update(year=cls.int_or_zero(val))
        if 'value' in data.keys():
            for key, val in data['value'].items():
                param = cls.objects.filter(
                    model_id=scenario.model_id,
                    scenario_id=scenario.id,
                    id=key)
                param.update(value=val)

    @classmethod
    def _delete(cls, scenario, data):
        """ Delete a scenario parameter """
        for p_id in data:
            cls.objects.filter(
                model_id=scenario.model_id,
                scenario_id=scenario.id,
                id=p_id).hard_delete()

    @staticmethod
    def int_or_zero(val):
        """ Force convert a value into an integer, and return 0 on failure """
        try:
            return int(val)
        except ValueError:
            return 0


class ParamsManager():

    @classmethod
    def all_tech_params(cls, tech):
        """ Builds data for the parameters table UI: Tech Level """
        p1, ids = cls.get_tech_params_dict('1_tech', tech.id)
        p0, _ = cls.get_tech_params_dict('0_abstract', tech.id, ids)
        essential_params, parameters = cls.parse_essentials(p1 + p0)
        return essential_params, parameters

    @classmethod
    def all_loc_tech_params(cls, loc_tech):
        """ Builds data for the parameters table UI: Loc Tech Level """
        tech_id = loc_tech.technology_id
        p2, ids = cls.get_tech_params_dict('2_loc_tech', loc_tech.id,
                                           systemwide=False)
        p1, ids = cls.get_tech_params_dict('1_tech', tech_id, ids,
                                           systemwide=False)
        p0, _ = cls.get_tech_params_dict('0_abstract', tech_id, ids,
                                         systemwide=False)
        _, parameters = cls.parse_essentials(p2 + p1 + p0)
        return parameters

    @staticmethod
    def get_tech_params_dict(level, id, excl_ids=None, systemwide=True):
        """ Builds data for the parameters table UI
        Levels: 2_loc_tech, 1_tech, 0_abstract
        excl_ids: Parameters IDs to exclude from return list
        systemwide: include system-wide parameters
        """
        data = []
        if excl_ids is None:
            excl_ids = []
        new_excl_ids = excl_ids.copy()

        # Get Params based on Level
        if level == '0_abstract':
            technology = Technology.objects.get(id=id)
            is_linear = technology.is_linear
            is_expansion = technology.is_expansion
            params = Abstract_Tech_Param.objects.filter(
                Q(abstract_tech=technology.abstract_tech),
                Q(parameter__is_linear=is_linear) | Q(parameter__is_linear=None),
                Q(parameter__is_expansion=is_expansion) | Q(parameter__is_expansion=None)
            ).order_by('parameter__category', 'parameter__pretty_name')

        elif level == '1_tech':
            technology = Technology.objects.get(id=id)
            params = Tech_Param.objects.filter(
                technology_id=id
            ).order_by('parameter__category', 'parameter__pretty_name', 'year')

        elif level == '2_loc_tech':
            loc_tech = Loc_Tech.objects.get(id=id)
            technology = loc_tech.technology
            params = Loc_Tech_Param.objects.filter(
                loc_tech_id=id
            ).order_by('parameter__category', 'parameter__pretty_name', 'year')

        # System-Wide Handling
        if systemwide is False:
            params = params.filter(parameter__is_systemwide=False)

        # Build Parameter Dictionary List
        for param in params:
            if (param.parameter_id in excl_ids):
                continue
            new_excl_ids.append(param.parameter_id)
            param_dict = {
                'id': param.id if 'id' in dir(param) else 0,
                'level': level,
                'year': param.year if 'year' in dir(param) else 0,
                'technology_id': technology.id,
                'parameter_root': param.parameter.root,
                'parameter_category': param.parameter.category,
                'parameter_id': param.parameter_id,
                'parameter_name': param.parameter.name,
                'parameter_pretty_name': param.parameter.pretty_name,
                'parameter_description': param.parameter.description,
                'parameter_is_essential': param.parameter.is_essential,
                'parameter_is_carrier': param.parameter.is_carrier,
                'units': param.parameter.units,
                'placeholder': param.placeholder if 'placeholder' in dir(param) else param.default_value,
                'choices': param.parameter.choices,
                'timeseries_enabled': param.parameter.timeseries_enabled,
                'timeseries': param.timeseries if 'timeseries' in dir(param) else False,
                'timeseries_meta_id': param.timeseries_meta_id if 'timeseries_meta_id' in dir(param) else 0,
                'value': param.value if 'value' in dir(param) else param.default_value}
            data.append(param_dict)

        return data, list(set(new_excl_ids))

    @staticmethod
    def parse_essentials(parameters):
        """ Parse out the essentials from the list returned from
        get_tech_params_dict() """

        p_df = pd.DataFrame(parameters)
        essentials_mask = p_df.parameter_is_essential == True
        # Parameters
        non_essentials_ids = p_df[~essentials_mask].index
        parameters = p_df.loc[non_essentials_ids].to_dict(orient='records')
        # Essentials
        essentials = {}
        essentials_ids = p_df[essentials_mask].index
        essential_params = p_df.loc[essentials_ids]
        carrier_ratios = essential_params[essential_params.parameter_id == 7]
        for _, row in essential_params.iterrows():
            ratios_val = None
            if row.parameter_id in [4, 5, 6, 66, 67, 68, 69]:
                val = row.value.split(',')
                try:
                    ratios = json.loads(carrier_ratios.value[0])
                    ratios_val = ratios[row.parameter_name]
                except Exception:
                    pass
            else:
                val = row.value
            essentials[row.parameter_id] = {
                'name': row.parameter_pretty_name,
                'value': val,
                'ratios': ratios_val,
                'description': row.parameter_description,
            }

        return essentials, parameters

    @staticmethod
    def simplify_name(name):
        simple_name = name.replace(' ', '_')
        simple_name = re.sub('\W+', '', simple_name)
        return simple_name
