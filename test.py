import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import time
from apirequest import get_metar, get_flight_by_callsign, get_f1_circuits, get_airport_info, get_pilots_summary, count_flights, filter_flights_by_airport, search_flight_by_user_id, search_flight_by_callsign


load_dotenv()
token = os.getenv('TKN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

@bot.command()
async def hola(ctx):
    await ctx.send(f"Hola \n{ctx.author.mention}!")

@bot.command()
async def comandos(ctx):
    commands_list = (
        "**Comandos disponibles:**\n"
        "1. `!comandos` - Muestra esta lista de comandos.\n"
        "2. `!metar <ICAO>` - Obtiene el reporte METAR para un aeropuerto específico (ejemplo: `!metar SCEL`).\n"
        "3. `!vuelo <callsign>` - Obtiene información de vuelo por callsign (ejemplo: `!vuelo LAN088`).\n"
        "4. `!circuits <query>` - Busca información sobre circuitos de F1 (ejemplo: `!circuits japan`).\n"
        "5. `!aeropuerto <ICAO>` - Obtiene información de un aeropuerto (ejemplo: `!aeropuerto KMCI`).\n"
        "6. `!poll <question>` - Crea una encuesta con reacciones.\n"
        "7. `!vuelos_totales` - Muestra el total de vuelos activos en IVAO.\n"
        "8. `!vuelos_aeropuerto <ICAO> [tipo]` - Filtra vuelos por aeropuerto (tipo: departure, arrival, alternative; por defecto: arrival).\n"
        "9. `!vuelo_usuario <user_id>` - Busca vuelo por ID de usuario en IVAO.\n"
        "10. `!vuelo_callsign <callsign>` - Busca vuelo por callsign en IVAO."
    )
    await ctx.send(commands_list)

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="Encuesta", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")
    await poll_message.add_reaction("🤷")

@bot.command()
async def metar(ctx, icao: str):
    icao = icao.strip().upper()
    if len(icao) != 4:
        await ctx.send("Por favor, envía un código ICAO de 4 caracteres, por ejemplo: `!metar SCEL`")
        return

    report = get_metar(icao)
    if not report:
        await ctx.send(f"No se encontró información METAR para `{icao}`.")
        return

    await ctx.send(report)


@bot.command()
async def vuelo(ctx, callsign: str):
    callsign = callsign.strip().upper()
    if not callsign:
        await ctx.send("Por favor, envía un callsign válido, por ejemplo: `!vuelo PTR2125`")
        return

    report = get_flight_by_callsign(callsign)
    if not report:
        await ctx.send(f"No se encontró información de vuelo para `{callsign}`.")
        return

    await ctx.send(report)


@bot.command()
async def circuits(ctx, *, query: str):
    if not query.strip():
        await ctx.send("Por favor, proporciona un término de búsqueda, por ejemplo: `!circuits japan`")
        return

    report = get_f1_circuits(query)
    await ctx.send(report)


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def aeropuerto(ctx, icao: str):
    icao = icao.strip().upper()
    if len(icao) != 4:
        await ctx.send("Por favor, envía un código ICAO de 4 caracteres, por ejemplo: `!aeropuerto KMCI`")
        return

    report = get_airport_info(icao)
    if not report:
        await ctx.send(f"No se encontró información para el aeropuerto `{icao}`.")
        return

    await ctx.send(report)


@bot.command()
async def vuelos_totales(ctx):
    data = get_pilots_summary()
    if data:
        total = count_flights(data)
        await ctx.send(f"Total de vuelos activos: {total}")
    else:
        await ctx.send("Error al obtener datos de vuelos.")


@bot.command()
async def vuelos_aeropuerto(ctx, icao: str, tipo: str = 'arrival'):
    icao = icao.strip().upper()
    if len(icao) != 4:
        await ctx.send("Por favor, envía un código ICAO de 4 caracteres, por ejemplo: `!vuelos_aeropuerto SCEL arrival`")
        return

    data = get_pilots_summary()
    if data:
        filtered = filter_flights_by_airport(data, icao, tipo)
        if filtered:
            await ctx.send(f"Vuelos con {tipo} en {icao}: {len(filtered)}")
            callsigns = [f['callsign'] for f in filtered[:5]]
            if callsigns:
                await ctx.send(f"Algunos: {', '.join(callsigns)}")
        else:
            await ctx.send(f"No se encontraron vuelos con {tipo} en {icao}")
    else:
        await ctx.send("Error al obtener datos de vuelos.")


@bot.command()
async def vuelo_usuario(ctx, user_id: int):
    data = get_pilots_summary()
    if data:
        flight = search_flight_by_user_id(data, user_id)
        if flight:
            callsign = flight.get('callsign', 'N/A')
            departure = flight.get('flightPlan', {}).get('departure', {}).get('icao', 'N/A')
            arrival = flight.get('flightPlan', {}).get('arrival', {}).get('icao', 'N/A')
            await ctx.send(f"Vuelo encontrado para usuario {user_id}: {callsign} de {departure} a {arrival}")
        else:
            await ctx.send(f"No se encontró vuelo para el usuario {user_id}")
    else:
        await ctx.send("Error al obtener datos de vuelos.")

@bot.command()
async def vuelo_callsign(ctx, callsign: str):
    callsign = callsign.strip().upper()
    if not callsign:
        await ctx.send("Por favor, envía un callsign válido, por ejemplo: `!vuelo_callsign PTR2125`")
        return

    data = get_pilots_summary()
    if data:
        flight = search_flight_by_callsign(data, callsign)
        if flight:
            departure = flight.get('flightPlan', {}).get('departure', {}).get('icao', 'N/A')
            arrival = flight.get('flightPlan', {}).get('arrival', {}).get('icao', 'N/A')
            status = flight.get('lastTrack', {}).get('state', 'N/A')
            altitude = flight.get('lastTrack', {}).get('altitude', 'N/A')
            groundspeed = flight.get('lastTrack', {}).get('groundSpeed', 'N/A')
            airplane = flight.get('flightPlan', {}).get('aircraft', {}).get('model', 'N/A')

            message = (
                f"✈️ **Vuelo: {callsign}**\n"
                f"🛫 De: {departure} → 🛬 a: {arrival}\n"
                f"📍 Estado: {status}\n"
                f"📊 Altitud: {altitude} ft\n"
                f"💨 Velocidad: {groundspeed} kt\n"
                f"🛩️ Avión: {airplane}"
            )
            await ctx.send(message)
        else:
            await ctx.send(f"No se encontró información de vuelo para `{callsign}`.")
    else:
        await ctx.send("Error al obtener datos de vuelos.")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)