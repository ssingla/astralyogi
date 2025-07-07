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
    # Build a `data` object manually
    data = type("AstroInput", (object,), {})()
    data.name = name
    data.date_of_birth = dob
    data.time_of_birth = tob
    data.city = city
    data.tz_offset = tz_offset
    data.adjust_dst = adjust_dst

    return get_astro_data(data)  # Call your existing function

def get_astro_data(data: AstroInput):
    try:
        location = geolocator.geocode(data.city)
        if not location:
            raise HTTPException(status_code=400, detail="City not found.")
        lat, lon = location.latitude, location.longitude

        dt = datetime.datetime.strptime(data.date_of_birth + " " + data.time_of_birth, "%Y-%m-%d %H:%M")
        hour = dt.hour + dt.minute / 60
        if data.adjust_dst and dt.year < 2000:
            data.tz_offset -= 0.5
        utc_hour = hour - data.tz_offset

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
        planet_degrees["Ketu"] = ketu_deg
        deg_str, sign = degree_to_sign_deg_min(ketu_deg)
        nak, pada = get_nakshatra_pada(ketu_deg)
        planet_data["Ketu"] = {
            "sign": sign,
            "degree": deg_str,
            "nakshatra": nak,
            "pada": pada
        }

        # Lagna
        ayanamsa = swe.get_ayanamsa(jd)
        lagna_tropical = swe.houses(jd, lat, lon)[0][0]
        lagna_sidereal = (lagna_tropical - ayanamsa) % 360
        lagna_deg_str, lagna_sign = degree_to_sign_deg_min(lagna_sidereal)

        # House mapping
        for planet, deg in planet_degrees.items():
            offset = (deg - lagna_sidereal) % 360
            house = int(offset // 30) + 1
            planet_data[planet]["house"] = house

    


  # === Vimshottari Dasha Calculation ===
        moon_deg = planet_degrees["Moon"]
        nak_index = int(moon_deg // (360 / 27))
        dasha_index = nak_index % 9
        percent_used = (moon_deg % (360 / 27)) / (360 / 27)
        rem_days = int(dasha_years[dasha_sequence[dasha_index]] * 365.25 * (1 - percent_used))

        def build_dasha_timeline(start_index, start_date):
            timeline = []
            index = start_index
            for _ in range(9):
                lord = dasha_sequence[index % 9]
                years = dasha_years[lord]
                days = int(years * 365.25)
                end_date = start_date + datetime.timedelta(days=days)
                timeline.append({
                    "mahadasha": lord,
                    "start": str(start_date),
                    "end": str(end_date)
                })
                start_date = end_date
                index += 1
            return timeline

        full_dasha_chart = build_dasha_timeline(dasha_index, dt.date() + datetime.timedelta(days=rem_days))

        # Find current dasha
        today = datetime.date.today()
        current_dasha = next(
            (d for d in full_dasha_chart if datetime.date.fromisoformat(d["start"]) <= today < datetime.date.fromisoformat(d["end"])),
            full_dasha_chart[-1]
        )# === Vimshottari Dasha ===
        moon_deg = planet_degrees["Moon"]
        nak_index = int(moon_deg // (360 / 27))
        dasha_index = nak_index % 9
        full_dasha = dasha_sequence[dasha_index]
        full_years = dasha_years[full_dasha]
        start_deg = nak_index * (360 / 27)
        percent_used = (moon_deg - start_deg) / (360 / 27)
        first_dasha_remaining = full_years * (1 - percent_used)
        first_dasha_days = int(first_dasha_remaining * 365.25)

        dasha_chart = []
        stack = []
        current_date = dt.date()
        today = datetime.date.today()

        for i in range(9):
            lord = dasha_sequence[(dasha_index + i) % 9]
            years = dasha_years[lord]
            if i == 0:
                days = first_dasha_days
            else:
                days = int(years * 365.25)
            end_date = current_date + datetime.timedelta(days=days)
            dasha_chart.append({
                "mahadasha": lord,
                "start": str(current_date),
                "end": str(end_date)
            })
            if current_date <= today < end_date:
                stack.append({"mahadasha": lord, "start": str(current_date), "end": str(end_date)})
            current_date = end_date

        # add placeholder for further stack (antardasha etc.)
        current_dasha = stack[-1] if stack else {}# === Yoga Detection ===
        yogas = []

        # Budh-Aditya Yoga: Sun + Mercury in same sign
        if planet_data["Sun"]["sign"] == planet_data["Mercury"]["sign"]:
            yogas.append({
                "name": "Budh-Aditya Yoga",
                "strength": 4.5  # Placeholder strength logic
            })

        # Gajakesari Yoga: Moon + Jupiter in Kendra from Lagna
        moon_house = planet_data["Moon"]["house"]
        jupiter_house = planet_data["Jupiter"]["house"]
        if abs(moon_house - jupiter_house) in [0, 3, 6, 9]:
            yogas.append({
                "name": "Gajakesari Yoga",
                "strength": 4.2
            })# === Divisional Charts: D9 (Navamsa) and D10 (Dasamsa) ===
        def get_divisional_sign(degree, division):
            segment = 30 / division
            index = int((degree % 30) // segment)
            sign = (int(degree // 30) * division + index) % 12
            return zodiac_signs[sign]

        divisional_charts = {
            "D9": {},
            "D10": {}
        }

        for planet, deg in planet_degrees.items():
            d9_sign = get_divisional_sign(deg, 9)
            d10_sign = get_divisional_sign(deg, 10)
            divisional_charts["D9"][planet] = d9_sign
            divisional_charts["D10"][planet] = d10_sign# === Gochar (Transits): Current sidereal planetary positions and houses ===
        today_dt = datetime.datetime.now()
        jd_today = swe.julday(today_dt.year, today_dt.month, today_dt.day, today_dt.hour + today_dt.minute / 60)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        transits = {}
        for name, pid in planet_ids.items():
            t_deg = swe.calc_ut(jd_today, pid, swe.FLG_SIDEREAL)[0][0] % 360
            t_deg_str, t_sign = degree_to_sign_deg_min(t_deg)
            offset = (t_deg - lagna_sidereal) % 360
            t_house = int(offset // 30) + 1
            transits[name] = {
                "sign": t_sign,
                "degree": t_deg_str,
                "house": t_house
            }

        # Add Ketu for transit (180 degrees opposite Rahu)
        rahu_transit_deg = swe.calc_ut(jd_today, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] % 360
        ketu_transit_deg = (rahu_transit_deg + 180) % 360
        ketu_sign, ketu_house = degree_to_sign_deg_min(ketu_transit_deg)[1], int(((ketu_transit_deg - lagna_sidereal) % 360) // 30) + 1
        transits["Ketu"] = {
            "sign": ketu_sign,
            "degree": degree_to_sign_deg_min(ketu_transit_deg)[0],
            "house": ketu_house
        }# === Retrograde + Combustion Status ===
        planet_status = {}
        for name, pid in planet_ids.items():
            pos, ret = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            deg = pos[0] % 360
            is_retro = bool(ret)

            # Combustion logic (simple placeholder):
            sun_deg = planet_degrees["Sun"]
            diff = abs((deg - sun_deg + 180) % 360 - 180)
            if name in ["Mercury", "Venus"]:
                combust_limit = 12 if name == "Mercury" else 10
            elif name in ["Mars", "Jupiter", "Saturn"]:
                combust_limit = 15
            else:
                combust_limit = 0  # No combustion for Moon, Rahu, Ketu

            is_combust = diff < combust_limit

            planet_status[name] = {
                "retrograde": is_retro,
                "combust": is_combust,
                "shadbala_score": 3.5  # Placeholder for now
            }

        planet_status["Ketu"] = {
            "retrograde": True,
            "combust": False,
            "shadbala_score": 3.0
        }# === Final Chart Structures (Grids) ===
        chart_grids = {
            "lagna_chart": {},
            "moon_chart": {},
            "chalit_chart": {},
            "navamsha_chart": {}
        }

        for planet, pdata in planet_data.items():
            h = pdata["house"]
            chart_grids["lagna_chart"].setdefault(str(h), []).append(planet)

        # Moon chart from Moon house
        moon_lagna_house = planet_data["Moon"]["house"]
        for planet, pdata in planet_data.items():
            rel_house = (pdata["house"] - moon_lagna_house + 12) % 12 + 1
            chart_grids["moon_chart"].setdefault(str(rel_house), []).append(planet)

        # Chalit chart (same as house positions for now)
        for planet, pdata in planet_data.items():
            chart_grids["chalit_chart"].setdefault(str(pdata["house"]), []).append(planet)

        # Navamsha chart by D-9 sign
        for planet, d9_sign in divisional_charts["D9"].items():
            chart_grids["navamsha_chart"].setdefault(d9_sign, []).append(planet)


        return {
            "profile": {
                "name": data.name,
                "dob": data.date_of_birth,
                "tob": data.time_of_birth,
                "city": data.city
            },
            "ascendant": {
                "sign": lagna_sign,
                "degree": lagna_deg_str
            },
            "planets": planet_data,
            "charts": chart_grids,
            "divisional_charts": divisional_charts,
            "transits": transits,
            "planet_status": planet_status,
            "house_strength": {},  # Placeholder for bhav bala
            "yogas": yogas,
            "current_dasha": current_dasha,
            "dasha_chart": dasha_chart
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
