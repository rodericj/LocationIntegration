from django.conf.urls.defaults import *
import os

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'LocationIntegration.historilator.views.start'),
    (r'^LocationIntegration/', 'LocationIntegration.historilator.views.index'),
    (r'^register/', 'LocationIntegration.historilator.views.register'),
    (r'^getFriends/', 'LocationIntegration.historilator.views.getFriends'),
    (r'^getMyCheckins/', 'LocationIntegration.historilator.views.getMyCheckins'),
    (r'^getUser/', 'LocationIntegration.historilator.views.getUser'),
    (r'^login/', 'django.views.generic.simple.direct_to_template', {'template':'login.html'}),
    (r'^addServices/', 'LocationIntegration.historilator.views.addServices'),
    (r'^auth/', 'LocationIntegration.historilator.views.auth'),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.getcwd()+'/site_media'}),


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
