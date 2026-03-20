import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm


class TrajectoryPlotter:

    def __init__(self):
        self.class_color_map = {}   # class_id -> color
        self.cmap = cm.get_cmap("hsv")

    # ---------------------------------------
    def _get_color(self, class_id):
        # Si ya existe -> usarlo
        if class_id in self.class_color_map:
            return self.class_color_map[class_id]

        # Generar nuevo color
        idx = len(self.class_color_map)
        color = self.cmap(idx * 0.61803398875 % 1.0)  # golden ratio spacing

        self.class_color_map[class_id] = color
        return color

    # ---------------------------------------
    def plot(self, df):
        plt.figure()

        grouped = df.groupby("tracker_id")

        for tracker_id, track in grouped:
            track = track.sort_values("frame")

            x = track["cx"].values
            y = track["cy"].values
            cls = int(track["class_id"].iloc[0])

            color = self._get_color(cls)

            n = len(x)
            alphas = np.linspace(0.15, 1.0, n)

            for i in range(n):
                plt.scatter(
                    x[i],
                    y[i],
                    color=color,
                    alpha=alphas[i],
                    s=30
                )

            plt.plot(x, y, color=color, alpha=0.35)

        plt.gca().invert_yaxis()
        plt.title(f"Trayectorias {n}")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()
