import requests
import json
from datetime import datetime
import pytz

# ======================================================================================================================
# F1
# ======================================================================================================================

def get_f1_circuits(query):
    query = query.strip()
    if not query:
        return "Por favor, proporciona un término de búsqueda válido."

    api_url = f"https://f1api.dev/api/circuits/search?q={query}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        if not response.text:
            print(f"Empty response from F1 API for query: {query}")
            return

        data = response.json()

        circuits = data.get('circuits', [])
        if not circuits:
            return f"No se encontraron circuitos para '{query}'."

        text = f"**Circuitos F1 encontrados para '{query}'** (Total: {data.get('total', 0)})\n\n"

        for circuit in circuits:
            circuit_id = circuit.get('circuitId', 'N/A')
            name = circuit.get('circuitName', 'N/A')
            country = circuit.get('country', 'N/A')
            city = circuit.get('city', 'N/A')
            length = circuit.get('circuitLength', 'N/A')
            if length != 'N/A':
                length = f"{length} m"
            lap_record = circuit.get('lapRecord', 'N/A')
            first_year = circuit.get('firstParticipationYear', 'N/A')
            corners = circuit.get('numberOfCorners', 'N/A')
            fastest_driver = circuit.get('fastestLapDriverId', 'N/A')
            fastest_team = circuit.get('fastestLapTeamId', 'N/A')
            fastest_year = circuit.get('fastestLapYear', 'N/A')
            url = circuit.get('url', 'N/A')

            text += (
                f"**{name}** ({circuit_id})\n"
                f"```ini\n"
                f"País          = {country}\n"
                f"Ciudad        = {city}\n"
                f"Longitud      = {length}\n"
                f"Record vuelta = {lap_record}\n"
                f"Primer año    = {first_year}\n"
                f"Número curvas = {corners}\n"
                f"Vuelta rápida = {fastest_driver} ({fastest_team}, {fastest_year})\n"
                f"URL           = {url}\n"
                f"```\n"
            )

        return text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the F1 API request: {e}")
        return f"Error al consultar la API de F1: {e}"
    except ValueError as e:
        print(f"JSON parse error for F1 API response: {e}")
        return "Error al procesar la respuesta de la API de F1."

def get_next_f1_race():
    """
    Obtiene la información de la próxima carrera de F1.
    """
    url = "https://f1api.dev/api/current"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        schedule = response.json()
        races = schedule['races']
        
        now = datetime.now(pytz.utc)
        
        next_race = None
        for race in races:
            race_date_str = race['schedule']['race']['date'] + 'T' + race['schedule']['race']['time']
            race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
            if race_date > now:
                next_race = race
                break
        
        if next_race:
            circuit_name = next_race['circuit']['circuitName']
            race_name = next_race['raceName']
            
            output = [
                f"**Próxima carrera:** {race_name}",
                f"**Circuito:** {circuit_name}",
                f"**Ubicación:** {next_race['circuit']['city']}, {next_race['circuit']['country']}",
                "**Horarios:**"
            ]
            
            sessions = {
                "FP1": "fp1",
                "FP2": "fp2",
                "FP3": "fp3",
                "Qualy": "qualy",
                "Carrera": "race"
            }
            
            sprint_sessions = {
                "Sprint Qualy": "sprintQualy",
                "Sprint Race": "sprintRace"
            }

            all_sessions = {}

            if next_race['schedule']['sprintRace']['date'] is not None:
                all_sessions.update(sprint_sessions)

            all_sessions.update(sessions)


            for session_name, session_key in all_sessions.items():
                session_info = next_race['schedule'][session_key]
                if session_info and session_info['date'] and session_info['time']:
                    session_date_str = session_info['date'] + 'T' + session_info['time']
                    session_date_utc = datetime.fromisoformat(session_date_str.replace('Z', '+00:00'))
                    output.append(f"- **{session_name}:** <t:{int(session_date_utc.timestamp())}:f>")
            
            return "\n".join(output)
        else:
            return "No hay próximas carreras en el calendario actual."
            
    except requests.exceptions.RequestException as e:
        return f"Error al contactar la API de F1: {e}"
    except (ValueError, IndexError, KeyError) as e:
        return f"Error al procesar la respuesta: {e}"


# ======================================================================================================================
# METAR
# ======================================================================================================================

def get_metar(icao):
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"

    try:
        response = requests.get(url)
        response.raise_for_status()

        if not response.text:
            print(f"Empty response from API for ICAO code: {icao}")
            return

        metar_data = response.json()

        if not metar_data:
            print(f"No data found for ICAO code: {icao}")
            return

        report = metar_data[0]
        text = (
            f"**METAR {icao}**\n"
            f"Temperatura: {report.get('temp', 'N/A')}°C\n"
            f"Punto de rocío: {report.get('dewp', 'N/A')}°C\n"
            f"Viento: {report.get('wdir', 'N/A')}° a {report.get('wspd', 'N/A')} kt\n"
            f"Visibilidad: {report.get('visib', 'N/A')}\n"
            f"Altímetro: {report.get('altim', 'N/A')} hPa\n"
            f"Raw: `{report.get('rawOb', 'N/A')}`"
        )
        return text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
    except (IndexError, KeyError) as e:
        print(f"Error parsing the weather data: {e}")

# ======================================================================================================================
# Aeropuertos
# ======================================================================================================================

def get_airport_info(icao):
    print(f"get_airport_info called for {icao}")
    icao = icao.strip().upper()
    api_url = f"https://aviationweather.gov/api/data/airport?ids={icao}&format=json"

    try:
        response =  requests.get(api_url, timeout=10)
        response.raise_for_status()

        if not response.text:
            print(f"Empty response from AviationWeather for ICAO: {icao}")
            return f"No se encontró información para el aeropuerto con código ICAO: {icao}"

        data = response.json()

        if not data:
            return f"No se encontró información para el aeropuerto con código ICAO: {icao}"

        airport = data[0]
        name = airport.get('name', 'N/A')
        iata_id = airport.get('iataId', 'N/A')
        state = airport.get('state', 'N/A')
        country = airport.get('country', 'N/A')
        lat = airport.get('lat', 'N/A')
        lon = airport.get('lon', 'N/A')
        elev = airport.get('elev', 'N/A')
        runways =airport.get('runways')

        text = (
            f"**Información del Aeropuerto: {name} ({icao})**\n"
            f"```ini\n"
            f"Código IATA   = {iata_id}\n"
            f"Ubicación     = {state}, {country}\n"
            f"Coordenadas   = {lat}, {lon}\n"
            f"Elevación     = {elev} m\n"
        )

      
        if runways:
            text += "[Pistas]\n"
            for runway in runways:
                runway_id = runway.get('id', 'N/A')
                dimension = runway.get('dimension', 'N/A')
                surface = runway.get('surface', 'N/A')
                text += (
                    f"{runway_id.ljust(14)}= {dimension}, Superficie: {surface}\n"
                )
        
        text += "```"

        return text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the AviationWeather API request: {e}")
        return f"Error al consultar la API de AviationWeather: {e}"
    except (ValueError, IndexError) as e:
        print(f"Error parsing JSON for AviationWeather response: {e}")
        return "Error al procesar la respuesta de la API de AviationWeather."


def get_flight_by_callsign(callsign):
    callsign = callsign.strip().upper()
    api_url = f"https://api.adsbdb.com/v0/callsign/{callsign}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        if not response.text:
            print(f"Empty response from ADSBDB for callsign: {callsign}")
            return

        payload = response.json()

        if not payload or 'response' not in payload:
            print(f"No response package for callsign: {callsign}")
            return

        flight = payload.get('response', {}).get('flightroute')
        if not flight:
            print(f"No flightroute data for callsign: {callsign}")
            return

        airline = flight.get('airline', {})
        origin = flight.get('origin', {})
        midpoint = flight.get('midpoint')
        destination = flight.get('destination', {})

        callsign_icao = flight.get('callsign_icao', 'N/A')
        callsign_iata = flight.get('callsign_iata', 'N/A')

        text = (
            f"**Vuelo {flight.get('callsign', callsign)} ({callsign_icao})**\n"
            f"```ini\n"
            f"Calls ign ICAO = {callsign_icao}\n"
            f"Callsign IATA = {callsign_iata}\n"
            f"Airline       = {airline.get('name', 'N/A')} ({airline.get('icao', 'N/A')})\n"
            f"Route         = {origin.get('icao_code', 'N/A')} → {destination.get('icao_code', 'N/A')}\n"
            f"Origen        = {origin.get('name', 'N/A')} ({origin.get('icao_code', 'N/A')}), {origin.get('country_name', 'N/A')}\n"
            f"Destino       = {destination.get('name', 'N/A')} ({destination.get('icao_code', 'N/A')}), {destination.get('country_name', 'N/A')}\n"
            f"Origen coords  = {origin.get('latitude', 'N/A')}, {origin.get('longitude', 'N/A')}\n"
            f"Destino coords = {destination.get('latitude', 'N/A')}, {destination.get('longitude', 'N/A')}\n"
        )

        if midpoint:
            text += (
                f"Midpoint      = {midpoint.get('name', 'N/A')} ({midpoint.get('icao_code', 'N/A')})\n"
                f"Midpoint coords = {midpoint.get('latitude', 'N/A')}, {midpoint.get('longitude', 'N/A')}\n"
            )

        text += "```"
        return text


    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the ADSBDB request: {e}")
        return
    except ValueError as e:
        print(f"JSON parse error for ADSBDB response: {e}")
        return

# ======================================================================================================================
# IVAO
# ======================================================================================================================

def get_pilots_summary():
    """
    Obtiene el resumen de pilotos de la API de IVAO.
    """
    url = "https://api.ivao.aero/v2/tracker/now/pilots/summary"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pilots summary: {e}")
        return None


def count_flights(data):
    if data is None:
        return 0
    return len(data)


def filter_flights_by_airport(data, icao, airport_type='departure'):

    if data is None:
        return []
    filtered = []
    for flight in data:
        fp = flight.get('flightPlan', {})
        airport = fp.get(airport_type)
        if airport and airport.get('icao') == icao.upper():
            filtered.append(flight)
    return filtered


def search_flight_by_user_id(data, user_id):
    if data is None:
        return None
    for flight in data:
        if flight.get('userId') == user_id:
            return flight
    return None

def search_flight_by_callsign(data, callsign):
    if data is None:
        return None
    for flight in data:
        if flight.get('callsign') == callsign:
            return flight
    return None
