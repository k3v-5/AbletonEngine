import server

conn = server.get_ableton_connection()

res = conn.send_command('execute_code', {
    'code': """
times_tested = []
for target in [0.0, 1.0, 4.0, 16.0, 64.0, 122.0, 128.0]:
    song.current_song_time = target
    times_tested.append((target, song.current_song_time))
result = times_tested
"""
})
print("Target vs Actual current_song_time:", res.get("result"))
