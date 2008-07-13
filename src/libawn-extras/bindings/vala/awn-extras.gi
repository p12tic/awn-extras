<?xml version="1.0"?>
<api version="1.0">
	<namespace name="AwnExtras">
		<function name="awncolor_to_string" symbol="awncolor_to_string">
			<return-type type="gchar*"/>
			<parameters>
				<parameter name="colour" type="AwnColor*"/>
			</parameters>
		</function>
		<function name="gdkcolor_to_awncolor" symbol="gdkcolor_to_awncolor">
			<return-type type="AwnColor"/>
			<parameters>
				<parameter name="gdk_colour" type="GdkColor*"/>
			</parameters>
		</function>
		<function name="gdkcolor_to_awncolor_with_alpha" symbol="gdkcolor_to_awncolor_with_alpha">
			<return-type type="AwnColor"/>
			<parameters>
				<parameter name="gdk_color" type="GdkColor*"/>
				<parameter name="alpha" type="double"/>
			</parameters>
		</function>
		<function name="get_pixbuf_from_surface" symbol="get_pixbuf_from_surface">
			<return-type type="GdkPixbuf*"/>
			<parameters>
				<parameter name="surface" type="cairo_surface_t*"/>
			</parameters>
		</function>
		<function name="notify_message" symbol="notify_message">
			<return-type type="gboolean"/>
			<parameters>
				<parameter name="summary" type="gchar*"/>
				<parameter name="body" type="gchar*"/>
				<parameter name="icon_str" type="gchar*"/>
				<parameter name="timeout" type="glong"/>
			</parameters>
		</function>
		<function name="notify_message_async" symbol="notify_message_async">
			<return-type type="void"/>
			<parameters>
				<parameter name="summary" type="gchar*"/>
				<parameter name="body" type="gchar*"/>
				<parameter name="icon_str" type="gchar*"/>
				<parameter name="timeout" type="glong"/>
			</parameters>
		</function>
		<function name="notify_message_extended" symbol="notify_message_extended">
			<return-type type="void"/>
			<parameters>
				<parameter name="summary" type="gchar*"/>
				<parameter name="body" type="gchar*"/>
				<parameter name="icon_str" type="gchar*"/>
				<parameter name="urgency" type="NotifyUrgency"/>
				<parameter name="timeout" type="glong"/>
				<parameter name="perror" type="GError**"/>
			</parameters>
		</function>
		<function name="share_config_bool" symbol="share_config_bool">
			<return-type type="gboolean"/>
			<parameters>
				<parameter name="key" type="gchar*"/>
			</parameters>
		</function>
		<function name="shared_menuitem_about_applet" symbol="shared_menuitem_about_applet">
			<return-type type="GtkWidget*"/>
			<parameters>
				<parameter name="copyright" type="gchar*"/>
				<parameter name="license" type="AwnAppletLicense"/>
				<parameter name="program_name" type="gchar*"/>
				<parameter name="version" type="gchar*"/>
				<parameter name="comments" type="gchar*"/>
				<parameter name="website" type="gchar*"/>
				<parameter name="website_label" type="gchar*"/>
				<parameter name="icon_name" type="gchar*"/>
				<parameter name="translator_credits" type="gchar*"/>
				<parameter name="authors" type="gchar**"/>
				<parameter name="artists" type="gchar**"/>
				<parameter name="documenters" type="gchar**"/>
			</parameters>
		</function>
		<function name="shared_menuitem_about_applet_simple" symbol="shared_menuitem_about_applet_simple">
			<return-type type="GtkWidget*"/>
			<parameters>
				<parameter name="copyright" type="gchar*"/>
				<parameter name="license" type="AwnAppletLicense"/>
				<parameter name="program_name" type="gchar*"/>
				<parameter name="version" type="gchar*"/>
			</parameters>
		</function>
		<function name="shared_menuitem_create_applet_prefs" symbol="shared_menuitem_create_applet_prefs">
			<return-type type="GtkWidget*"/>
			<parameters>
				<parameter name="instance" type="gchar*"/>
				<parameter name="baseconf" type="gchar*"/>
				<parameter name="applet_name" type="gchar*"/>
			</parameters>
		</function>
		<function name="surface_2_pixbuf" symbol="surface_2_pixbuf">
			<return-type type="GdkPixbuf*"/>
			<parameters>
				<parameter name="pixbuf" type="GdkPixbuf*"/>
				<parameter name="surface" type="cairo_surface_t*"/>
			</parameters>
		</function>
		<function name="urldecode" symbol="urldecode">
			<return-type type="char*"/>
			<parameters>
				<parameter name="source" type="char*"/>
				<parameter name="dest" type="char*"/>
			</parameters>
		</function>
		<function name="urlencode" symbol="urlencode">
			<return-type type="char*"/>
			<parameters>
				<parameter name="source" type="char*"/>
				<parameter name="dest" type="char*"/>
				<parameter name="max" type="unsigned"/>
			</parameters>
		</function>
		<enum name="AwnAppletLicense">
			<member name="AWN_APPLET_LICENSE_GPLV2" value="10"/>
			<member name="AWN_APPLET_LICENSE_GPLV3" value="11"/>
			<member name="AWN_APPLET_LICENSE_LGPLV2_1" value="12"/>
			<member name="AWN_APPLET_LICENSE_LGPLV3" value="13"/>
		</enum>
	</namespace>
</api>
