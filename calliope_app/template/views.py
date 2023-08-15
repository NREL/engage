import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from api.utils import initialize_units, convert_units_no_pipe
from api.models.configuration import Model, Model_User, Location, Model_Comment, Technology, Abstract_Tech, Loc_Tech, Tech_Param, Loc_Tech_Param, ParamsManager, Carrier
from template.models import Template, Template_Variable, Template_Type, Template_Type_Variable, Template_Type_Loc, Template_Type_Tech, Template_Type_Loc_Tech, Template_Type_Parameter, Template_Type_Carrier

@login_required
@csrf_protect
def model_templates(request):
    """
    Get "Templates" data

    Returns: JsonResponse

    Example:
    GET: /model/templates/
    """
    
    model_uuid = request.GET['model_uuid']
    model = Model.by_uuid(model_uuid)
    templates = list(Template.objects.filter(model_id=model.id).values('id', 'name', 'template_type', 'model', 'location', 'created', 'updated'))
    model_template_ids = Template.objects.filter(model_id=model.id).values_list('id', flat=True)
    template_variables = list(Template_Variable.objects.filter(template__in=model_template_ids).values('id', 'template', 'template_type_variable', 'value', 'raw_value', 'timeseries', 'timeseries_meta', 'updated'))

    template_types = list(Template_Type.objects.all().values('id', 'name', 'pretty_name', 'description'))
    template_type_variables = list(Template_Type_Variable.objects.all().values('id', 'name', 'pretty_name', 'template_type', 'units', 'default_value', 'min', 'max', 'category', 'choices', 'description', 'timeseries_enabled'))
    template_type_locs = list(Template_Type_Loc.objects.all().values('id', 'name', 'template_type', 'latitude_offset', 'longitude_offset'))
    template_type_techs = list(Template_Type_Tech.objects.all().values('id', 'name', 'description', 'template_type', 'version_tag', 'abstract_tech', 'energy_carrier', 'carrier_in', 'carrier_out', 'carrier_in_2', 'carrier_out_2', 'carrier_in_3', 'carrier_out_3', 'carrier_ratios'))
    template_type_loc_techs = list(Template_Type_Loc_Tech.objects.all().values('id', 'template_type', 'template_loc_1', 'template_loc_2', 'template_tech'))
    template_type_parameters = list(Template_Type_Parameter.objects.all().values('id', 'template_loc_tech', 'parameter', 'equation'))
    locations = list(Location.objects.filter(model_id=model.id).values('id', 'pretty_name', 'name', 'latitude', 'longitude', 'available_area', 'model', 'created', 'updated', 'template_id', 'template_type_loc_id'))

    response = {
        'model_uuid ': model_uuid, 
        "templates": templates,
        "template_variables": template_variables,
        "template_types": template_types,
        "template_type_variables": template_type_variables,
        "template_type_locs": template_type_locs,
        "template_type_techs": template_type_techs,
        "template_type_loc_techs": template_type_loc_techs,
        "template_type_parameters": template_type_parameters,
        "locations": locations,
    }

    return JsonResponse(response, safe=False)

@login_required
@csrf_protect
def delete_template(request):
    """
    Delete a template.

    Parameters:
    template_id (int)

    Returns (json): Action Confirmation

    Example:
    POST: /model/templates/delete/
    """
    template_id = request.POST.get("template_id", False)
    template = Template.objects.filter(id=template_id).first()
    if template_id is False:
        raise ValidationError(f"Error: Template ID has not been provided.")

    # Loop through techs 
    technologies = Technology.objects.filter(template_type_id=template.template_type_id, model_id=template.model)

    #NOTE: any updates to this section of code should also be made for tempaltes post_delete
    for tech in technologies:
        # Delete if there are no other nodes outside of the template are using this tech
        loc_techs = Loc_Tech.objects.filter(technology=tech)
        uniqueToTemplate = True
        for loc_tech in loc_techs:
            if loc_tech.template_id != int(template_id):
                print("tech not unique to template loc_tech.template_id: " + str(loc_tech.template_id) + " template_id: " + str(template_id))
                uniqueToTemplate = False
                break
        
        if uniqueToTemplate:
            Technology.objects.filter(id=tech.id).delete()

    # Delete any remaining nodes, locations and the template itself
    Loc_Tech.objects.filter(template_id=template_id).delete()
    Location.objects.filter(template_id=template_id).delete()
    template.delete()
    
    payload = {"message": "deleted template",
                "template_id": template.id,
                }

    return HttpResponse(json.dumps(payload), content_type="application/json")


@login_required
@csrf_protect
def add_template(request):
    """
    Add a new template.

    Parameters:
    model_uuid (uuid): required
    template_id (int): optional
    name: required
    template_type_id: required
    location: required

    Returns (json): Action Confirmation

    Example:
    POST: /model/templates/create/
    """

    template = {}
    model_uuid = request.POST.get("model_uuid", False)
    if model_uuid is False:
        raise ValidationError(f"Error: Model UUID has not been provided.")
    
    template_id = request.POST.get("template_id", False)
    name = request.POST["name"]
    template_type_id = request.POST["template_type"]
    location_id = request.POST["location"]
    varData = json.loads(request.POST["form_data"])
    templateVars = []
    if varData:
        templateVars = varData['templateVars']

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)
    template_type = Template_Type.objects.filter(id=template_type_id).first()
    location = Location.objects.filter(id=location_id).first()
    template_type_locs = list(Template_Type_Loc.objects.filter(template_type_id=template_type_id).values('id', 'name', 'template_type', 'latitude_offset', 'longitude_offset'))
    template_type_techs = list(Template_Type_Tech.objects.filter(template_type_id=template_type_id).values('id', 'name', 'description', 'template_type', 'version_tag', 'abstract_tech', 'energy_carrier', 'carrier_in', 'carrier_out', 'carrier_in_2', 'carrier_out_2', 'carrier_in_3', 'carrier_out_3', 'carrier_ratios'))
    template_type_loc_techs = list(Template_Type_Loc_Tech.objects.filter(template_type_id=template_type_id).values('id', 'template_type', 'template_loc_1', 'template_loc_2', 'template_tech'))
    template_type_carriers = list(Template_Type_Carrier.objects.filter(template_type_id=template_type_id).values('id', 'template_type', 'name', 'description', 'rate_unit', 'quantity_unit'))
    
    if template_id:
        print ("Editing a template: " + template_id)
        template = Template.objects.filter(id=template_id).first()
        if template is not None:
            Template.objects.filter(id=template_id).update(
                name=name,
            )

        new_template_variables = update_template_variables(templateVars, template)

        # TODO: return to to edit nodes with a template
        # template_loc_techs = Loc_Tech.objects.filter(template_id=template_id)
        # if template_loc_techs is not None:
        #     ureg = initialize_units()
        #     for template_loc_tech_id, loc_tech in template_loc_techs.items():
        #         template_type_parameters = Template_Type_Parameter.objects.filter(template_loc_tech_id=template_loc_tech_id)
        #         for template_type_parameter in template_type_parameters: 
        #             equation = template_type_parameter.equation
        #             for name, template_variable in new_template_variables.items(): 
        #                 equation = equation.replace('||'+name+'||', template_variable.value)
        #             value, rawValue  = convert_units_no_pipe(ureg, equation, template_type_parameter.parameter.units)
        #             Loc_Tech_Param.objects.filter(model=model, loc_tech=loc_tech, parameter=template_type_parameter.parameter).update(
        #                 value=value,
        #                 raw_value=rawValue,
        #             )

        comment = "{} updated a template: {} of template type: {}.".format(
            request.user.get_full_name(),
            name,
            template_type.pretty_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="add")
        model.notify_collaborators(request.user)
    else:
        print ("Creating a new template")
        template = Template.objects.create(
            name=name,
            template_type=template_type,
            model=model,
            location=location,
        )

        new_locations = get_or_create_template_locations(template_type_locs, model, name, location, template)
        new_technologies = get_or_create_template_technologies(template_type_techs, model, template_type_id)
        new_carriers = get_or_create_template_carriers(template_type_carriers, model, template_type_id)
        new_loc_techs = create_template_loc_techs(template_type_loc_techs, model, name, template_type_id, template)
        new_template_variables = create_template_variables(templateVars, template)

        if new_loc_techs is not None:
            ureg = initialize_units()
            #ureg.Quantity("6 kW")
            for template_loc_tech_id, loc_tech in new_loc_techs.items():
                template_type_parameters = Template_Type_Parameter.objects.filter(template_loc_tech_id=template_loc_tech_id)
  
                # get input and output carriers
                units_in_ids = [4,5,70]
                units_out_ids = [4,6,71]
                tech_param_in = Tech_Param.objects.filter(model=model, technology=loc_tech.technology, parameter_id__in=units_in_ids).first()
                tech_param_out = Tech_Param.objects.filter(model=model, technology=loc_tech.technology, parameter_id__in=units_out_ids).first()
                carrier_in = {"rate_unit": "kW", "quantity_unit": "kWh"}
                carrier_out = {"rate_unit": "kW", "quantity_unit": "kWh"}
                if tech_param_in:
                    carrier_in["rate_unit"] = new_carriers.get(tech_param_in.value, carrier_in).rate_unit
                    carrier_in["quantity_unit"] = new_carriers.get(tech_param_in.value, carrier_in).quantity_unit
                if tech_param_out:
                    carrier_out["rate_unit"] = new_carriers.get(tech_param_out.value, carrier_out).rate_unit
                    carrier_out["quantity_unit"] = new_carriers.get(tech_param_out.value, carrier_out).quantity_unit
                
                # set all custom parameters for the new node
                for template_type_parameter in template_type_parameters: 
                    equation = template_type_parameter.equation

                    # check for variables in equation to replac
                    for name, template_variable in new_template_variables.items():
                        equation = equation.replace('||'+name+'||', template_variable.value)

                    # override carrier placeholder strings with units from carrier where applicable
                    units = template_type_parameter.parameter.units.replace('[[in_rate]]',carrier_in["rate_unit"]).replace('[[in_quantity]]',carrier_in["quantity_unit"]).replace('[[out_quantity]]',carrier_out["quantity_unit"]).replace('[[out_rate]]',carrier_out["rate_unit"])
                    value, rawValue  = convert_units_no_pipe(ureg, equation, units)
                    Loc_Tech_Param.objects.create(
                        parameter=template_type_parameter.parameter,
                        loc_tech=loc_tech,
                        value=value,
                        raw_value=rawValue,
                        model=model,
                    )

        # Log Activity
        comment = "{} added a template: {} of template type: {}.".format(
            request.user.get_full_name(),
            name,
            template_type.pretty_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="add")
        model.notify_collaborators(request.user)

    # Return new list of active loc tech IDs
    request.session["template_id"] = template.id
    payload = {"message": "added template",
                "template_id": template.id,
                }

    return HttpResponse(json.dumps(payload), content_type="application/json")

def create_template_variables(templateVars, template):
    new_template_variables = {}
    for templateVar in templateVars:
        new_template_var = Template_Variable.objects.create(
            template_type_variable_id=templateVar["id"],
            value=templateVar["value"],
            raw_value=templateVar["value"],
            template_id=template.id,
        )
        new_template_variables[new_template_var.template_type_variable.name] = new_template_var
    return new_template_variables

def update_template_variables(templateVars, template):
    updated_template_variables = {}
    for templateVar in templateVars:
        new_template_var = Template_Variable.objects.filter(template_id=template.id, template_type_variable_id=templateVar["id"]).update(
            value=templateVar["value"],
            raw_value=templateVar["value"],
        )
        updated_template_variables[templateVar["id"]] = new_template_var
    return updated_template_variables

def get_or_create_template_locations(template_type_locs, model, name, location, template):
    new_locations = {}
    for template_type_loc in template_type_locs:
        lat = location.latitude+template_type_loc['latitude_offset']
        if (lat > 90):
            lat = 90
        elif (lat < -90):
            lat = -90
        long = location.longitude+template_type_loc['longitude_offset']
        if (long > 180): 
            long = 180 
        elif (long < -180):
            long = -180 
        new_location = Location.objects.create(
            pretty_name=name + ' - ' + template_type_loc['name'],
            name=template_type_loc['name'].replace(' ', '-'),
            latitude=lat, 
            longitude=long, 
            model=model,
            template_id=template.id,
            template_type_loc_id=template_type_loc['id'],
        )
        new_locations[template_type_loc['id']] = new_location
    return new_locations

# Create template technologies
def get_or_create_template_technologies(template_type_techs, model, template_type_id):
    new_technologies = {}
    for template_type_tech in template_type_techs:
        existingTech = Technology.objects.filter(model_id=model.id, template_type_id=template_type_id, template_type_tech_id=template_type_tech['id']).first()

        if existingTech is None:
            abstract_tech = Abstract_Tech.objects.filter(
                    id=template_type_tech['id']).first()
            if template_type_tech['version_tag'] is not None:
                new_tech = Technology.objects.create(
                    abstract_tech=abstract_tech,
                    pretty_name=template_type_tech['name'],
                    name=template_type_tech['name'].replace(' ', '-'),
                    model=model,
                    description=template_type_tech['description'],
                    template_type_id=template_type_id,
                    template_type_tech_id=template_type_tech['id'],
                    tag=ParamsManager.simplify_name(template_type_tech['version_tag']),
                    pretty_tag=template_type_tech['version_tag']
                )
            else:
                new_tech = Technology.objects.create(
                    abstract_tech=abstract_tech,
                    pretty_name=template_type_tech['name'],
                    name=template_type_tech['name'].replace(' ', '-'),
                    model=model,
                    description=template_type_tech['description'],
                    template_type_id=template_type_id,
                    template_type_tech_id=template_type_tech['id'],
                )

            new_technologies[template_type_tech['id']] = new_tech

            #set 'name' and 'parent' paramters
            Tech_Param.objects.create(
                model=model,
                technology=new_tech,
                parameter_id=1,
                value=abstract_tech.name,
            )

            #set technology params from template parameters
            if template_type_tech['version_tag'] is not None:
                Tech_Param.objects.create(
                    model=model, 
                    technology=new_tech, 
                    parameter_id=2, 
                    value=new_tech.pretty_name + " [" + template_type_tech['version_tag'] + "]"
                )
            else:
                Tech_Param.objects.create(
                    model=model,
                    technology=new_tech,
                    parameter_id=2,
                    value=new_tech.pretty_name
                )

            if template_type_tech['energy_carrier'] is not None:
                Tech_Param.objects.create(
                    model=model, 
                    technology=new_tech, 
                    parameter_id=4, 
                    value=template_type_tech['energy_carrier']
                )
            if template_type_tech['carrier_in'] is not None:
                Tech_Param.objects.create(
                    model=model, 
                    technology=new_tech, 
                    parameter_id=5, 
                    value=template_type_tech['carrier_in']
                )
            if template_type_tech['carrier_out'] is not None:
                Tech_Param.objects.create(
                    model=model,
                    technology=new_tech,
                    parameter_id=6,
                    value=template_type_tech['carrier_out']
                )
            if template_type_tech['carrier_in_2'] is not None:
                Tech_Param.objects.create(
                    model=model, 
                    technology=new_tech, 
                    parameter_id=66, 
                    value=template_type_tech['carrier_in_2']
                )
            if template_type_tech['carrier_out_2'] is not None:
                Tech_Param.objects.create(
                    model=model,
                    technology=new_tech,
                    parameter_id=67,
                    value=template_type_tech['carrier_out_2']
                )
            if template_type_tech['carrier_in_3'] is not None:
                Tech_Param.objects.create(
                    model=model, 
                    technology=new_tech, 
                    parameter_id=68, 
                    value=template_type_tech['carrier_in_3']
                )
            if template_type_tech['carrier_out_3'] is not None:
                Tech_Param.objects.create(
                    model=model,
                    technology=new_tech,
                    parameter_id=69,
                    value=template_type_tech['carrier_out_3']
                )
            if template_type_tech['carrier_ratios'] is not None:
                Tech_Param.objects.create(
                    model=model,
                    technology=new_tech,
                    parameter_id=7,
                    value=template_type_tech['carrier_ratios']
                )
    return new_technologies

def get_or_create_template_carriers(template_type_carriers, model, template_type_id):
    new_carriers = {}
    modelCarriers = Carrier.objects.filter(model_id=model.id).all()

    for carrier in template_type_carriers:
        existingCarrier = modelCarriers.filter(name=carrier['name']).first()
        if existingCarrier: 
            new_carriers[existingCarrier.name] = existingCarrier
            continue
        
        new_carrier = Carrier.objects.create(
            model=model,
            name=carrier['name'],
            description=carrier['description'],
            rate_unit=carrier['rate_unit'],
            quantity_unit=carrier['quantity_unit'],
        )
        new_carriers[new_carrier.name] = new_carrier
    return new_carriers

def create_template_loc_techs(template_type_loc_techs, model, name, template_type_id, template):
    new_loc_techs = {}

    for template_type_loc_tech in template_type_loc_techs:
        if template_type_loc_tech['template_loc_2']:
            new_loc_tech = Loc_Tech.objects.create(
                model=model,
                technology=Technology.objects.filter(model_id=model.id, template_type_id=template_type_id, template_type_tech_id=template_type_loc_tech['template_tech']).first(),
                location_1=Location.objects.filter(model_id=model.id, template_id=template.id, template_type_loc_id=template_type_loc_tech['template_loc_1']).first(),
                location_2=Location.objects.filter(model_id=model.id, template_id=template.id, template_type_loc_id=template_type_loc_tech['template_loc_2']).first(),
                description="Node created by " + name + " template",
                template_id=template.id,
                template_type_loc_tech_id=template_type_loc_tech['id'],
            )
        else:
            new_loc_tech = Loc_Tech.objects.create(
                model=model,
                technology=Technology.objects.filter(model_id=model.id, template_type_id=template_type_id, template_type_tech_id=template_type_loc_tech['template_tech']).first(),
                location_1=Location.objects.filter(model_id=model.id, template_id=template.id, template_type_loc_id=template_type_loc_tech['template_loc_1']).first(),
                description="Node created by " + name + " template",
                template_id=template.id,
                template_type_loc_tech_id=template_type_loc_tech['id'],
            )
        print ("new_loc_tech.id " + str(new_loc_tech.id))
        new_loc_techs[template_type_loc_tech['id']] = new_loc_tech

    return new_loc_techs