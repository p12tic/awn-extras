//
// AwnIcon.cs
//
// Copyright (c) 2008 Randal Barlow
//
// Permission is hereby granted, free of charge, to any person
// obtaining a copy of this software and associated documentation
// files (the "Software"), to deal in the Software without
// restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following
// conditions:
//
// The above copyright notice and this permission notice shall be
// included in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
// OTHER DEALINGS IN THE SOFTWARE.

using System;
using System.IO;
using Mono.Unix;

using NDesk.DBus;

using Hyena;
using Banshee.Base;
using Banshee.ServiceStack;
using Banshee.Collection;
using Banshee.MediaEngine;

namespace Banshee.AwnIcon
{
    [Interface ("com.google.code.Awn")]
    public interface AvantWindowNavigator
    {
        void SetTaskIconByName (string app, string icon);
        void UnsetTaskIconByName (string app);
        void SetInfoByName (string app, string info);        
        void UnsetInfoByName (string app);        
    }

    public class AwnIconService : IExtensionService, IDisposable
    {
        string taskname = "nereid";
        private AvantWindowNavigator awn;
        
        public AwnIconService ()
        {
        }
        
        void IExtensionService.Initialize ()
        {
            Console.WriteLine("[AWN] It worked");
            awn = Bus.Session.GetObject<AvantWindowNavigator> ("com.google.code.Awn", new ObjectPath ("/com/google/code/Awn"));
            ServiceManager.PlaybackController.Transition += OnPlayerUpdate;
            ServiceManager.PlaybackController.TrackStarted += OnPlayerUpdate;
            ServiceManager.PlayerEngine.ConnectEvent (OnTrackInfoUpdated, PlayerEvent.TrackInfoUpdated);
        }
        
        public void Dispose ()
        {
            ServiceManager.PlaybackController.Transition -= OnPlayerUpdate;
            ServiceManager.PlaybackController.TrackStarted -= OnPlayerUpdate;
        }

        private void OnPlayerUpdate (object o, EventArgs args)
            
        {
            try{
                UnSetAwnIcon ();
                SetAwnIcon ();
            }
            catch (Exception e){
            }
        }

        private void OnTrackInfoUpdated (PlayerEventArgs args)
        {
            try{
                SetAwnIcon ();
            }
            catch (Exception e){
            }
        }

        // Set the awn icon
        private void SetAwnIcon ()
        {
            if (awn != null && ServiceManager.PlaybackController.CurrentTrack != null &&
                File.Exists (CoverArtSpec.GetPath(ServiceManager.PlaybackController.CurrentTrack.ArtworkId))) {
                awn.SetTaskIconByName (taskname, CoverArtSpec.GetPath (ServiceManager.PlaybackController.CurrentTrack.ArtworkId));
            }
        }

        // Unset the awn icon
        private void UnSetAwnIcon ()
        {
            if (awn != null){
                awn.UnsetTaskIconByName (taskname);
                awn.UnsetInfoByName (taskname);
            }
        }
        
        string IService.ServiceName {
            get { return "AwnIconService"; }
        }        
    }
}