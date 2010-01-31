# Copyright (C) 2010  onox <denkpadje@gmail.com>
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.
#
# (Based on code released to the public domain by Paul Schlyter, December 1992
# http://stjarnhimlen.se/comp/sunriset.c)

import math


def sun_rise_set(year, month, day, lon, lat, altit=-35.0/60.0, upper_limb=1):
    """Return sunrise and sunset times as a tuple.

    Sunrise/set is considered to occur when the Sun's upper limb is
    35 arc minutes below the horizon (this accounts for the refraction
    of the Earth's atmosphere).

    Civil twilight: -6.0, 0
    Nautical twilight: -12.0, 0
    Astronomical twilight: -18.0, 0

    Note: year,month,date = calendar date, 1801-2099 only.
          Eastern longitude positive, Western longitude negative
              Northern latitude positive, Southern latitude negative
          The longitude value IS critical in this function!
          altit = the altitude which the Sun should cross
                  Set to -35/60 degrees for rise/set, -6 degrees
              for civil, -12 degrees for nautical and -18
              degrees for astronomical twilight.
            upper_limb: non-zero -> upper limb, zero -> center
              Set to non-zero (e.g. 1) when computing rise/set
              times, and to zero when computing start/end of
              twilight.
          *rise = where to store the rise time
          *set  = where to store the set  time
                  Both times are relative to the specified altitude,
              and thus this function can be used to compute
              various twilight times, as well as rise/set times
    Return value:  0 = sun rises/sets this day, times stored at
                           *trise and *tset.
              +1 = sun above the specified 'horizon' 24 hours.
                   *trise set to time when the sun is at south,
               minus 12 hours while *tset is set to the south
               time plus 12 hours. 'Day' length = 24 hours
              -1 = sun is below the specified 'horizon' 24 hours
                   'Day' length = 0 hours, *trise and *tset are
                both set to the time when the sun is at south.

    """
    RADEG  = 180.0 / math.pi
    DEGRAD = math.pi / 180.0
    INV360 = 1.0 / 360.0

    sind   = lambda x: math.sin(x * DEGRAD)
    cosd   = lambda x: math.cos(x * DEGRAD)
    acosd  = lambda x: math.acos(x) * RADEG
    atan2d = lambda x, y: math.atan2(x, y) * RADEG

    def days_since_2000_jan_0(y, m, d):
        """Compute the number of days elapsed since 2000 Jan 0.0
        (which is equal to 1999 Dec 31, 0h UT)

        """
        return (367*(y)-((7*((y)+(((m)+9)/12)))/4)+((275*(m))/9)+(d)-730530)

    def revolution(x):
        """Reduce angle to within 0..360 degrees.

        """
        return x - 360.0 * math.floor(x * INV360)

    def rev180(x):
        """Reduce angle to within -180..+180 degrees.

        """
        return x - 360.0 * math.floor(x * INV360 + 0.5)

    def sunpos(d):
        """Compute the Sun's ecliptic longitude and distance
        at an instant given in d, number of days since
        2000 Jan 0.0.  The Sun's ecliptic latitude is not
        computed, since it's always very near 0.

        """
        # Compute mean elements
        M = revolution(356.0470 + 0.9856002585 * d)
        w = 282.9404 + 4.70935E-5 * d
        e = 0.016709 - 1.151E-9 * d

        # Compute true longitude and radius vector
        E = M + e * RADEG * sind(M) * (1.0 + e * cosd(M))
        x = cosd(E) - e
        y = math.sqrt(1.0 - e*e) * sind(E)
        r = math.sqrt(x*x + y*y)  # solar distance
        v = atan2d(y, x)  # true anomaly

        lon = v + w  # true solar longitude
        if lon >= 360.0:
            lon -= 360.0  # make it 0..360 degrees

        return (lon, r)

    def sun_ra_dec(d):
        """Return the angle of the Sun (RA)
        the declination (dec) and the distance of the Sun (r)
        for a given day d.

        """
        # Compute Sun's ecliptical coordinates (true solar longitude, solar distance)
        lon, r = sunpos(d)

        # Compute ecliptic rectangular coordinates (z=0)
        x = r * cosd(lon)
        y = r * sind(lon)

        # Compute obliquity of ecliptic (inclination of Earth's axis)
        obl_ecl = 23.4393 - 3.563E-7 * d

        # Convert to equatorial rectangular coordinates - x is unchanged
        z = y * sind(obl_ecl)
        y = y * cosd(obl_ecl)

        # Convert to spherical coordinates
        ra = atan2d(y, x)
        dec = atan2d(z, math.sqrt(x*x + y*y))

        return (ra, dec, r)

    def GMST0(d):
        """This function computes GMST0, the Greenwich Mean Sidereal Time
        at 0h UT (i.e. the sidereal time at the Greenwhich meridian at
        0h UT).  GMST is then the sidereal time at Greenwich at any
        time of the day.  I've generalized GMST0 as well, and define it
        as:  GMST0 = GMST - UT  --  this allows GMST0 to be computed at
        other times than 0h UT as well.  While this sounds somewhat
        contradictory, it is very practical:  instead of computing
        GMST like:

         GMST = (GMST0) + UT * (366.2422/365.2422)

        where (GMST0) is the GMST last time UT was 0 hours, one simply
        computes:

         GMST = GMST0 + UT

        where GMST0 is the GMST "at 0h UT" but at the current moment!
        Defined in this way, GMST0 will increase with about 4 min a
        day.  It also happens that GMST0 (in degrees, 1 hr = 15 degr)
        is equal to the Sun's mean longitude plus/minus 180 degrees!
        (if we neglect aberration, which amounts to 20 seconds of arc
        or 1.33 seconds of time)

        """
        # Sidtime at 0h UT = L (Sun's mean longitude) + 180.0 degr
        # L = M + w, as defined in sunpos()
        return revolution((180.0 + 356.0470 + 282.9404) + (0.9856002585 + 4.70935E-5) * d)

    # Compute d of 12h local mean solar time
    d = days_since_2000_jan_0(year, month, day) + 0.5 - (lon/360.0)

    # Compute local sidereal time of this moment
    sidtime = revolution(GMST0(d) + 180.0 + lon)

    # Compute Sun's RA + Decl at this moment
    sra, sdec, sr = sun_ra_dec(d)

    # Compute time when Sun is at south - in hours UT
    tsouth = 12.0 - rev180(sidtime - sra) / 15.0

    # Compute the Sun's apparent radius, degrees
    sradius = 0.2666 / sr

    # Do correction to upper limb, if necessary
    if upper_limb:
        altit -= sradius

    # Compute the diurnal arc that the Sun traverses to reach
    # the specified altitude altit:
    cost = (sind(altit) - sind(lat) * sind(sdec)) / (cosd(lat) * cosd(sdec))

    if cost >= 1.0:
        t = 0.0  # sun always below altit
    elif cost <= -1.0:
        t = 12.0  # sun always above altit
    else:
        t = acosd(cost) / 15.0  # the diurnal arc, hours

    # Store rise and set times - in hours UT
    return (tsouth - t, tsouth + t)
