from geopy.geocoders import Nominatim
import swisseph as swe
import datetime

zodiac_signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

nakshatras = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

dasha_sequence = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

dasha_years = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

geolocator = Nominatim(user_agent="astralyogi")

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

def get_astrology_profile(name, date_of_birth, time_of_birth, city, tz_offset=5.5, adjust_dst=False):
    try:
        location = geolocator.geocode(city)
        if not location:
            return {"error": "City not found."}
        lat, lon = location.latitude, location.longitude

        dt = datetime.datetime.strptime(date_of_birth + " " + time_of_birth, "%Y-%m-%d %H:%M")
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

        for name, pid in planet_ids.items():
            pos = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            degree = pos[0][0] % 360
            planet_degrees[name] = degree
            deg_str, sign = degree_to_sign_deg_min(degree)
            nak, pada = get_nakshatra_pada(degree)
            planet_data[name] = {
                "sign": sign,
                "degree": deg_str,
                "nakshatra": nak,
                "pada": pada
            }

        # Add Ketu
        ketu_deg = (planet_degrees["Rahu"] + 180) % 360
        deg_str, sign = degree_to_sign_deg_min(ketu_deg)
        nak, pada = get_nakshatra_pada(ketu_deg)
        planet_data["Ketu"] = {
            "sign": sign,
            "degree": deg_str,
            "nakshatra": nak,
            "pada": pada
        }

        ayanamsa = swe.get_ayanamsa(jd)
        lagna_tropical = swe.houses(jd, lat, lon)[0][0]
        lagna_sidereal = (lagna_tropical - ayanamsa) % 360
        lagna_str, lagna_sign = degree_to_sign_deg_min(lagna_sidereal)

        for planet, deg in planet_degrees.items():
            offset = (deg - lagna_sidereal) % 360
            house = int(offset // 30) + 1
            planet_data[planet]["house"] = house

        ketu_offset = (ketu_deg - lagna_sidereal) % 360
        planet_data["Ketu"]["house"] = int(ketu_offset // 30) + 1

        # Vimshottari Mahadasha
        moon_deg = planet_degrees["Moon"]
        nak_index = int(moon_deg // (360 / 27))
        dasha_index = nak_index % 9
        start_deg = nak_index * (360 / 27)
        percent_used = (moon_deg - start_deg) / (360 / 27)
        remaining = dasha_years[dasha_sequence[dasha_index]] * (1 - percent_used)
        start_date = dt.date()
        dasha_chart = []

        for i in range(9):
            lord = dasha_sequence[(dasha_index + i) % 9]
            years = dasha_years[lord]
            days = int(remaining * 365.25) if i == 0 else int(years * 365.25)
            end_date = start_date + datetime.timedelta(days=days)
            dasha_chart.append({
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
            "dob": date_of_birth,
            "tob": time_of_birth,
            "city": city,
            "ascendant": {
                "sign": lagna_sign,
                "degree": lagna_str
            },
            "planets": planet_data,
            "current_dasha": current_dasha,
            "dasha_chart": dasha_chart
        }

    except Exception as e:
        return {"error": str(e)}