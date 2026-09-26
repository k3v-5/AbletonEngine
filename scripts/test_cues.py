import server

conn = server.get_ableton_connection()
res = conn.send_command('execute_code', {
    'code': "result = [a for a in dir(song) if 'cue' in a.lower()]"
})
print("Cue attributes on song:", res.get("result"))

cue_points = conn.send_command('execute_code', {
    'code': "result = [{'name': c.name, 'time': c.time} for c in song.cue_points]"
})
print("Current cue points:", cue_points.get("result"))
