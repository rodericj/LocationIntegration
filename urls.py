from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'Location_Integration.historilator.views.start'),
    (r'^Location_Integration/', 'Location_Integration.historilator.views.index'),
    (r'^register/', 'Location_Integration.historilator.views.register'),
    (r'^test/', 'Location_Integration.historilator.views.test'),
    (r'^login/', 'django.views.generic.simple.direct_to_template', {'template':'login.html'}),
    (r'^addServices/', 'Location_Integration.historilator.views.addServices'),
    (r'^auth/', 'Location_Integration.historilator.views.auth'),
    #(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/Users/roderic/dev/Location-Integration/force_quared/force_quared/media'}),


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
