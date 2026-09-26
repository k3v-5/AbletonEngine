import server

conn = server.get_ableton_connection()
cue_points = conn.send_command('execute_code', {
    'code': "result = [(c.name, c.time, repr(c.time), abs(c.time - 64.0)) for c in song.cue_points]"
})
print("Detailed cues:", cue_points.get("result"))
