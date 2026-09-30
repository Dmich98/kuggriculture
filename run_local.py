from pathlib import Path

from kaggle_environments import make


env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run(["main.py", "starter"])

for player, state in enumerate(env.steps[-1]):
    print(f"Player {player}: reward={state.reward}, status={state.status}")

html = env.render(mode="html", width=1200, height=800)
Path("game.html").write_text(html, encoding="utf-8")
print("Visualization saved to game.html")
