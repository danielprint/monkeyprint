"""
Description:
  Provides a pyGtk vtkRenderWindowInteractor widget.  This embeds a
  vtkRenderWindow inside a GTK widget and uses the
  vtkGenericRenderWindowInteractor for the event handling.  This is
  similar to GtkVTKRenderWindowInteractor.py.
  The extensions here allow the use of gtkglext rather than gtkgl and
  pygtk-2 rather than pygtk-0.  It requires pygtk-2.0.0 or later.
  There is a working example at the bottom.
Credits:
  John Hunter <jdhunter@ace.bsd.uchicago.edu> developed and tested
  this code based on VTK's GtkVTKRenderWindow.py and extended it to
  work with pygtk-2.0.0.
License:
  VTK license.
"""

import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkGLExt', '1.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, Gdk, GtkGLExt, GdkX11, GLib
import vtk

class GtkGLExtVTKRenderWindowInteractor(GtkGLExt.DrawingArea):

    """ Embeds a vtkRenderWindow into a pyGTK widget and uses
    vtkGenericRenderWindowInteractor for the event handling.  This
    class embeds the RenderWindow correctly.  A __getattr__ hook is
    provided that makes the class behave like a
    vtkGenericRenderWindowInteractor."""

    def __init__(self, *args):
        GtkGLExt.DrawingArea.__init__(self)

        self.set_double_buffered(False)

        self._RenderWindow = vtk.vtkRenderWindow()

        # private attributes
        self.__Created = 0
        self._ActiveButton = 0

        self._Iren = vtk.vtkGenericRenderWindowInteractor()
        self._Iren.SetRenderWindow(self._RenderWindow)
        self._Iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self._Iren.AddObserver('CreateTimerEvent', self.CreateTimer)
        self._Iren.AddObserver('DestroyTimerEvent', self.DestroyTimer)
        self.ConnectSignals()

        # need this to be able to handle key_press events.
        self.set_can_focus(True)

    def set_size_request(self, w, h):
        GtkGLExt.DrawingArea.set_size_request(self, w, h)
        self._RenderWindow.SetSize(w, h)
        self._Iren.SetSize(w, h)
        self._Iren.ConfigureEvent()

    def ConnectSignals(self):
        self.connect("realize", self.OnRealize)
        self.connect("expose_event", self.OnExpose)
        self.connect("configure_event", self.OnConfigure)
        self.connect("button_press_event", self.OnButtonDown)
        self.connect("button_release_event", self.OnButtonUp)
        self.connect("motion_notify_event", self.OnMouseMove)
        self.connect("enter_notify_event", self.OnEnter)
        self.connect("leave_notify_event", self.OnLeave)
        self.connect("key_press_event", self.OnKeyPress)
        self.connect("key_release_event", self.OnKeyRelease)
        self.connect("delete_event", self.OnDestroy)
        self.add_events(
            Gdk.EventMask.EXPOSURE_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_HINT_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

    def __getattr__(self, attr):
        """Makes the object behave like a
        vtkGenericRenderWindowInteractor"""
        if attr == '__vtk__':
            return lambda t=self._Iren: t
        elif hasattr(self._Iren, attr):
            return getattr(self._Iren, attr)
        else:
            raise AttributeError(self.__class__.__name__ +
                  " has no attribute named " + attr)

    def CreateTimer(self, obj, event):
        GLib.timeout_add(10, self._Iren.TimerEvent)

    def DestroyTimer(self, obj, event):
        """The timer is a one shot timer so will expire automatically."""
        return True

    def GetRenderWindow(self):
        return self._RenderWindow

    def Render(self):
        if self.__Created:
            self._RenderWindow.Render()

    def OnRealize(self, *args):
        if self.__Created == 0:
            # you can't get the xid without the window being realized.
            self.realize()
            window = self.get_window()
            if sys.platform == 'win32':
                win_id = str(int(window.get_handle()))
            else:
                win_id = str(window.get_xid())

            self._RenderWindow.SetWindowInfo(win_id)
            #self._Iren.Initialize()
            self.__Created = 1
        return True

    def OnConfigure(self, widget, event):
        self.widget=widget
        self._Iren.SetSize(event.width, event.height)
        self._Iren.ConfigureEvent()
        self.Render()
        return True

    def OnExpose(self, *args):
        self.Render()
        return True

    def OnDestroy(self, event=None):
        self.hide()
        del self._RenderWindow
        self.destroy()
        return True

    def _GetCtrlShift(self, event):
        ctrl, shift = 0, 0
        if ((event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK):
            ctrl = 1
        if ((event.state & Gdk.ModifierType.SHIFT_MASK) == Gdk.ModifierType.SHIFT_MASK):
            shift = 1
        return ctrl, shift

    def OnButtonDown(self, wid, event):
        """Mouse button pressed."""
        x, y = int(event.x), int(event.y)
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            chr(0), 0, None)
        button = event.button
        if button == 3:
            self._Iren.RightButtonPressEvent()
            return True
        elif button == 1:
            self._Iren.LeftButtonPressEvent()
            return True
        elif button == 2:
            self._Iren.MiddleButtonPressEvent()
            return True
        else:
            return False

    def OnButtonUp(self, wid, event):
        """Mouse button released."""
        x, y = int(event.x), int(event.y)
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            chr(0), 0, None)
        button = event.button
        if button == 3:
            self._Iren.RightButtonReleaseEvent()
            return True
        elif button == 1:
            self._Iren.LeftButtonReleaseEvent()
            return True
        elif button == 2:
            self._Iren.MiddleButtonReleaseEvent()
            return True

        return False

    def OnMouseMove(self, wid, event):
        """Mouse has moved."""
        x, y = int(event.x), int(event.y)
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.MouseMoveEvent()
        return True

    def OnEnter(self, wid, event):
        """Entering the vtkRenderWindow."""
        self.grab_focus()
        x, y = int(event.x), int(event.y)
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.EnterEvent()
        return True

    def OnLeave(self, wid, event):
        """Leaving the vtkRenderWindow."""
        x, y = int(event.x), int(event.y)
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.LeaveEvent()
        return True

    def OnKeyPress(self, wid, event):
        """Key pressed."""
        ctrl, shift = self._GetCtrlShift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        x = int(getattr(event, 'x', 0))
        y = int(getattr(event, 'y', 0))
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            key, 0, keysym)
        self._Iren.KeyPressEvent()
        self._Iren.CharEvent()
        return True

    def OnKeyRelease(self, wid, event):
        "Key released."
        ctrl, shift = self._GetCtrlShift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        x = int(getattr(event, 'x', 0))
        y = int(getattr(event, 'y', 0))
        self._Iren.SetEventInformationFlipY(x, y, ctrl, shift,
                                            key, 0, keysym)
        self._Iren.KeyReleaseEvent()
        return True

    def Initialize(self):
        if self.__Created:
            self._Iren.Initialize()

    def SetPicker(self, picker):
        self._Iren.SetPicker(picker)

    def GetPicker(self, picker):
        return self._Iren.GetPicker()
