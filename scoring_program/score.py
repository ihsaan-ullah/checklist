# ------------------------------------------
# Imports
# ------------------------------------------
import os
import json
from datetime import datetime as dt
import matplotlib.pyplot as plt
import sys
import io
import base64

# ------------------------------------------
# Settings
# ------------------------------------------
# True when running on Codabench
CODABENCH = False


class Scoring:
    def __init__(self):
        # Initialize class variables
        self.start_time = None
        self.end_time = None
        self.scores_dict = {}

    def start_timer(self):
        self.start_time = dt.now()

    def stop_timer(self):
        self.end_time = dt.now()

    def get_duration(self):
        if self.start_time is None:
            print("[-] Timer was never started. Returning None")
            return None

        if self.end_time is None:
            print("[-] Timer was never stoped. Returning None")
            return None

        return self.end_time - self.start_time

    def show_duration(self):
        print("\n---------------------------------")
        print(f"[✔] Total duration: {self.get_duration()}")
        print("---------------------------------")

    def set_directories(self):

        # set default directories for Codabench
        module_dir = os.path.dirname(os.path.realpath(__file__))
        root_dir_name = os.path.dirname(module_dir)

        score_file_name = "scores.json"
        html_file_name = "detailed_results.html"

        output_dir_name = "scoring_output"
        reference_dir_name = "reference_data"
        predictions_dir_name = "sample_result_submission"

        if CODABENCH:
            root_dir_name = "/app"
            output_dir_name = "output"
            reference_dir_name = 'input/ref'
            predictions_dir_name = 'input/res'

        # Directory to output computed score into
        self.output_dir = os.path.join(root_dir_name, output_dir_name)
        # reference data (test labels)
        self.reference_dir = os.path.join(root_dir_name, reference_dir_name)
        # submitted/predicted labels
        self.prediction_dir = os.path.join(root_dir_name, predictions_dir_name)

        # score file to write score into
        self.score_file = os.path.join(self.output_dir, score_file_name)
        # html file to write score and figures into
        self.html_file = os.path.join(self.output_dir, html_file_name)

        # Add to path
        sys.path.append(self.reference_dir)
        sys.path.append(self.output_dir)
        sys.path.append(self.prediction_dir)

    def write_scores(self):
        print("[*] Writing scores")

        with open(self.score_file, "w") as f_score:
            f_score.write(json.dumps(self.scores_dict, indent=4))

        print("[✔]")

    def write_html(self, content):
        with open(self.html_file, 'a', encoding="utf-8") as f:
            f.write(content)

    def _print(self, content):
        print(content)
        self.write_html(content + "<br>")

    def save_figure(self, mu, p16s, p84s, set=0):
        fig = plt.figure(figsize=(5, 5))
        # plot horizontal lines from p16 to p84
        for i, (p16, p84) in enumerate(zip(p16s, p84s)):
            plt.hlines(y=i, xmin=p16, xmax=p84, colors='b')
        plt.vlines(x=mu, ymin=0, ymax=len(p16s), colors='r', linestyles='dashed', label="average $\mu$")
        plt.xlabel('mu')
        plt.ylabel('psuedo-experiments')
        plt.title(f'mu distribution - Set {set}')
        plt.legend()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        fig_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        self.write_html(f"<img src='data:image/png;base64,{fig_b64}'><br>")


if __name__ == "__main__":
    print("############################################")
    print("### Scoring Program")
    print("############################################\n")

    # Init scoring
    scoring = Scoring()

    # Set directories
    scoring.set_directories()

    # Start timer
    scoring.start_timer()

    # Write scores
    scoring.write_scores()

    # Stop timer
    scoring.stop_timer()

    # Show duration
    scoring.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Scoring Program executed successfully!")
    print("----------------------------------------------\n\n")
