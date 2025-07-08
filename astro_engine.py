from geopy.geocoders import Nominatim
import swisseph as swe
import datetime

zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
              "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
              "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

dasha_sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
dasha_years = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}


def degree_to_sign_deg_min(degree):
    sign_index = int(degree // 30)
    sign = zodiac_signs[sign_index]
    deg_in_sign = degree % 30
    deg = int(deg_in_sign)
    minute = int((deg_in_sign - deg) * 60)
    return f"{sign} {deg}°{minute}′", sign


def get_nakshatra_pada(degree):
    index = int(degree // (360 / 27))
    pada = int((degree % (360 / 27)) // ((360 / 27) / 4)) + 1
    return nakshatras[index], pada


def get_astrology_profile(name, dob, tob, city, tz_offset=5.5, adjust_dst=False):
    try:
        geolocator = Nominatim(user_agent="astralyogi")
        location = geolocator.geocode(city)
        if not location:
            return {"error": "City not found."}

        lat, lon = location.latitude, location.longitude
        dt = datetime.datetime.strptime(dob + " " + tob, "%Y-%m-%d %H:%M")
        hour = dt.hour + dt.minute / 60
        if adjust_dst and dt.year < 2000:
            tz_offset -= 0.5
        utc_hour = hour - tz_offset

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        swe.set_topo(lon, lat, 0)
        jd = swe.julday(dt.year, dt.month, dt.day, utc_hour)

        planet_ids = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }

        planet_data = {}
        planet_degrees = {}
        ayanamsa = swe.get_ayanamsa(jd)

        for name_, pid in planet_ids.items():
            pos, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            degree = pos[0] % 360
            planet_degrees[name_] = degree
            deg_str, sign = degree_to_sign_deg_min(degree)
            nak, pada = get_nakshatra_pada(degree)

            retro = pos[3] < 0  # negative speed → retrograde
            combust = False  # placeholder; real combustion logic can be added

            planet_data[name_] = {
                "sign": sign,
                "degree": deg_str,
                "nakshatra": nak,
                "pada": pada,
                "retrograde": retro,
                "combust": combust
            }

        # Ketu (180 degrees opposite to Rahu)
        ketu_deg = (planet_degrees["Rahu"] + 180) % 360
        deg_str, sign = degree_to_sign_deg_min(ketu_deg)
        nak, pada = get_nakshatra_pada(ketu_deg)
        planet_data["Ketu"] = {
            "sign": sign,
            "degree": deg_str,
            "nakshatra": nak,
            "pada": pada,
            "retrograde": True,
            "combust": False
        }

        lagna_tropical = swe.houses(jd, lat, lon)[0][0]
        lagna_sidereal = (lagna_tropical - ayanamsa) % 360
        lagna_str, lagna_sign = degree_to_sign_deg_min(lagna_sidereal)

        for planet, deg in planet_degrees.items():
            offset = (deg - lagna_sidereal) % 360
            house = int(offset // 30) + 1
            planet_data[planet]["house"] = house

        # Vimshottari Dasha Tree (Mahadasha to Pratyantar)
        moon_deg = planet_degrees["Moon"]
        nak_index = int(moon_deg // (360 / 27))
        dasha_index = nak_index % 9
        full_dasha = []
        start_deg = nak_index * (360 / 27)
        percent_used = (moon_deg - start_deg) / (360 / 27)
        remaining = dasha_years[dasha_sequence[dasha_index]] * (1 - percent_used)
        start_date = dt.date()

        for i in range(9):
            lord = dasha_sequence[(dasha_index + i) % 9]
            years = dasha_years[lord]
            days = int(remaining * 365.25) if i == 0 else int(years * 365.25)
            end_date = start_date + datetime.timedelta(days=days)
            full_dasha.append({
                "mahadasha": lord,
                "start": str(start_date),
                "end": str(end_date)
            })
            if start_date <= datetime.date.today() < end_date:
                current_dasha = {
                    "mahadasha": lord,
                    "start": str(start_date),
                    "end": str(end_date)
                }
            start_date = end_date

        return {
            "name": name,
            "dob": dob,
            "tob": tob,
            "city": city,
            "ascendant": {
                "sign": lagna_sign,
                "degree": lagna_str
            },
            "planets": planet_data,
            "current_dasha": current_dasha,
            "dasha_chart": full_dasha,
            "gpt_profile": {
                "ascendant_sign": lagna_sign,
                "moon_nakshatra": planet_data["Moon"]["nakshatra"],
                "moon_house": planet_data["Moon"]["house"],
                "moon_pada": planet_data["Moon"]["pada"],
                "current_mahadasha": current_dasha["mahadasha"],
                "planetary_strengths": {
                    key: {
                        "sign": val["sign"],
                        "house": val["house"],
                        "retrograde": val["retrograde"],
                        "combust": val["combust"]
                    } for key, val in planet_data.items()
                }
            }
        }

    except Exception as e:
        return {"error": str(e)}