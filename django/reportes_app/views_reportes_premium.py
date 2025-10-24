from __future__ import unicode_literals
import os

from django.shortcuts import redirect
from django.views.generic import FormView

from ominicontacto_app.models import AgenteProfile, Campana, Grupo
from reportes_app.models import LlamadaLog
from ominicontacto_app.utiles import convert_fecha_datetime, fecha_local

from reportes_app.forms import ReportePremiumForm

class ReportesPremium(FormView):
    """
    Esta vista tiene los reportes premium implementados por Havzeit
    """

    template_name = 'reporte_premium1.html'
    form_class = ReportePremiumForm
    
    
    def get_form_kwargs(self):
        kwargs = super(ReportesPremium, self).get_form_kwargs()
        return kwargs   
  
  
    def get_context_data(self, **kwargs):
        context = super(ReportesPremium, self).get_context_data(**kwargs)
        
        campanas_activas = Campana.objects.all()
        
        supervisor = self.request.user.get_supervisor_profile()
        agentes_activos = AgenteProfile.objects.obtener_agentes_supervisor(
           supervisor).select_related('user')
        
        grupos_agente = Grupo.objects.all()
        
        context['agentes'] = agentes_activos
        context['campanas'] = campanas_activas
        context['grupos_agente'] = grupos_agente
        context['survey_app_activado'] = not os.getenv('SURVEY_VERSION', '') == ''
        
        context.update(kwargs)
        
        return context
    
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            fecha = form.cleaned_data.get('fecha')

            # Separar el rango de fechas
            fecha_desde, fecha_hasta = fecha.split(' - ')  # importante: espacio antes y después del guion
            fecha_desde = convert_fecha_datetime(fecha_desde)
            fecha_hasta = convert_fecha_datetime(fecha_hasta)
            
            # Capturar el resto de campos desde el POST
            tipo_campana_id = request.POST.get('tipo_campana')
            campana_id = request.POST.get('campana')
            agente_id = request.POST.get('agente')
            grupo_agente_id = request.POST.get('grupo_agente')
            incluir_sin_campana = request.POST.get('incluir_sin_campana') == 'on'
            phone = request.POST.get('phone')
            call_id = request.POST.get('call_id')

            # Llamar a tu función de reporte
            graficos_campana = LlamadaLog.objects.obtener_campanas_tipo_campana_campana_agente_fecha( 
                tipo_campana_id=tipo_campana_id,
                campana_id=campana_id,
                agente_id=agente_id,
                incluir_sin_campana=incluir_sin_campana,
                phone=phone,
                call_id=call_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )

            # Preparar contexto
            # context = self.get_context_data(
            #     graficos_campana=graficos_campana,
            #     campana_id=campana_id,
            #     agente_id=agente_id,
            #     grupo_id=grupo_agente_id,
            #     form=form
            # )
            # Enviar todo al contexto (para mantener los valores seleccionados)
            context = self.get_context_data(
                graficos_campana=graficos_campana,
                form=form,
                tipo_campana_id=tipo_campana_id,
                campana_id=campana_id,
                agente_id=agente_id,
                grupo_id=grupo_agente_id,
                incluir_sin_campana=incluir_sin_campana,
                phone=phone,
                call_id=call_id
            )
            
            return self.render_to_response(context)
        
        # Si el form no es válido
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    
    def exporta_reporte_campana(request, tipo_reporte):
        """
        Esta vista invoca a generar un csv de reporte premium de campañas
        """
        service = ReporteAgenteCSVService()
        url = service.obtener_url_reporte_csv_descargar(tipo_reporte)
        return redirect(url)