/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */

/* cpu-dialog.c */

#include <glibtop/proclist.h>

#include "cpu-dialog.h"
#include "util.h"

G_DEFINE_TYPE (AwnCPUDialog, awn_cpu_dialog, AWN_TYPE_DIALOG)

#define AWN_CPU_DIALOG_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CPU_DIALOG, AwnCPUDialogPrivate))

typedef struct _AwnCPUDialogPrivate AwnCPUDialogPrivate;

struct _AwnCPUDialogPrivate 
{
  GtkWidget * scroll;
  GtkWidget * table;
  
  guint     num_entries;
  
  gboolean  show_root;
  gboolean  show_other;
  guint     timeout_id;
  
};


static void awn_cpu_dialog_populate_table (AwnCPUDialog *dialog);


static void
awn_cpu_dialog_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_cpu_dialog_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_cpu_dialog_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->dispose (object);
}

static void
awn_cpu_dialog_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->finalize (object);
}


static gboolean
awn_cpu_dialog_expose(AwnCPUDialog * dialog,GdkEventExpose *event,gpointer null)
{
  awn_cpu_dialog_populate_table (dialog);
  return FALSE;
}

static gboolean
awn_cpu_dialog_show(AwnCPUDialog * dialog,gpointer null)
{
  AwnCPUDialogPrivate * priv = AWN_CPU_DIALOG_GET_PRIVATE (dialog);

  if (!priv->timeout_id)
  {
    priv->timeout_id = g_timeout_add_seconds (1, (GSourceFunc)gtk_widget_queue_draw,dialog);
  }
  return FALSE;
}


static void
awn_cpu_dialog_constructed (GObject *object)
{
  AwnCPUDialogPrivate * priv = AWN_CPU_DIALOG_GET_PRIVATE (object);
  
  if (G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->constructed )
  {
    G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->constructed (object);
  }  

  priv->scroll = gtk_scrolled_window_new (NULL,NULL);
  gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW(priv->scroll),
                                  GTK_POLICY_NEVER,GTK_POLICY_NEVER);

  gtk_container_add (GTK_CONTAINER(object), priv->scroll);  
  
  priv->table = gtk_table_new (9,priv->num_entries,FALSE);

  gtk_scrolled_window_add_with_viewport (GTK_SCROLLED_WINDOW (priv->scroll),
                                         priv->table);  
  update_process_info();  
  awn_cpu_dialog_populate_table (AWN_CPU_DIALOG(object));

  gtk_widget_show_all (priv->scroll);
  g_signal_connect (object,"expose-event",G_CALLBACK(awn_cpu_dialog_expose),NULL);
  g_signal_connect (object,"show",G_CALLBACK(awn_cpu_dialog_show),NULL);
}

static void
awn_cpu_dialog_class_init (AwnCPUDialogClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnCPUDialogPrivate));

  object_class->get_property = awn_cpu_dialog_get_property;
  object_class->set_property = awn_cpu_dialog_set_property;
  object_class->dispose = awn_cpu_dialog_dispose;
  object_class->finalize = awn_cpu_dialog_finalize;
  object_class->constructed = awn_cpu_dialog_constructed;
}

static void
awn_cpu_dialog_init (AwnCPUDialog *self)
{
  AwnCPUDialogPrivate * priv = AWN_CPU_DIALOG_GET_PRIVATE (self);
  priv->num_entries = 20;

}

AwnCPUDialog*
awn_cpu_dialog_new (GtkWidget *widget)
{
  return g_object_new (AWN_TYPE_CPU_DIALOG, 
                       "anchor", widget,
                       NULL);
}


AwnCPUDialog*
awn_cpu_dialog_new_with_applet (GtkWidget *widget, AwnApplet * applet)
{
  return g_object_new (AWN_TYPE_CPU_DIALOG, 
                       "anchor-applet", applet,
                       "anchor", widget,
                       NULL);
}

static void awn_cpu_dialog_populate_table (AwnCPUDialog *dialog)
{
  AwnCPUDialogPrivate * priv = AWN_CPU_DIALOG_GET_PRIVATE (dialog);
  GList * iter;
  gint    y=0;
  GtkWidget * new_table;

  if (!GTK_WIDGET_VISIBLE(dialog))
  {
    g_debug ("%s: not visible.  bailing",__func__);
    return;
  }
  new_table = gtk_table_new (9,priv->num_entries,FALSE);    

  gtk_table_attach_defaults (GTK_TABLE(new_table),
                             gtk_button_new_with_label ("PID"),
                                            0,
                                            1,
                                            0,
                                            1);
  gtk_table_attach_defaults (GTK_TABLE(new_table),
                             gtk_button_new_with_label ("Process Name"),
                                            1,
                                            2,
                                            0,
                                            1);
  gtk_table_attach_defaults (GTK_TABLE(new_table),
                             gtk_button_new_with_label ("CPU"),
                                            2,
                                            3,
                                            0,
                                            1);
  
  for (iter = get_process_info(); iter&& y<20; iter=iter->next)
  {
    AwnProcInfo * data = iter->data;
    gchar *text = g_strdup_printf ("%d",data->pid);
    gtk_table_attach_defaults (GTK_TABLE(new_table),
                                gtk_label_new (text),
                                0,
                                1,
                                1+y,
                                2+y);
    g_free (text);
    text = g_strdup_printf ("%s",data->proc_state.cmd);
    gtk_table_attach_defaults (GTK_TABLE(new_table),
                                gtk_label_new (text),
                                1,
                                2,  
                                1+y,
                                2+y);
    g_free (text);    
    text = g_strdup_printf ("%0.1lf",data->percent_cpu);
    gtk_table_attach_defaults (GTK_TABLE(new_table),
                                gtk_label_new (text),
                                2,
                                3,  
                                1+y,
                                2+y);
    y++;
    g_free (text);
  }
  
  gtk_widget_destroy (priv->table);
  priv->table = new_table;
  gtk_widget_show_all (priv->table);
  gtk_scrolled_window_add_with_viewport (GTK_SCROLLED_WINDOW (priv->scroll),
                                         priv->table);  
  
}