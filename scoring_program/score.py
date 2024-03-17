# ------------------------------------------
# Imports
# ------------------------------------------
import os
import json
from datetime import datetime as dt
import sys
import io
import pandas as pd

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

    def load_ingestion_result(self):
        print("[*] Reading ingestion result")

        ingestion_result_file = os.path.join(self.prediction_dir, "checklist.csv")
        self.ingestion_df = pd.read_csv(ingestion_result_file)

        print("[✔]")

    def write_reviews_to_html(self):

        print("[*] Writing reviews to detailed result")
        for index, row in self.ingestion_df.iterrows():
            self._print("--------------------------------------")
            self._print(f"Question:{row['Question']}")
            self._print(f"Answer:{row['Answer']}")
            self._print(f"Justification:{row['Justification']}")
            self._print(f"Review:{row['Review']}")
            self._print(f"Correctness Score:{row['Correctness_Score']}")
            self._print("--------------------------------------")
        print("[✔]")

    def compute_completeness_rate(self):
        print("[*] Computing Rate of Completeness")

        total_answers = len(self.ingestion_df)
        incomplete_answers = 0

        for index, row in self.ingestion_df.iterrows():
            if row["Answer"] in ["TODO", "Not Found"] or row["Justification"] in ["TODO", "Not Found"]:
                incomplete_answers += 1

        completion_rate = ((total_answers - incomplete_answers) / total_answers) * 100
        self.scores_dict["completion_rate"] = completion_rate
        self._print("--------------------------------------")
        self._print(f"Completion Rate: {completion_rate}")
        self._print("--------------------------------------")

        print("[✔]")

    def compute_correctness_rate(self):
        print("[*] Computing Rate of Correctness")

        correctness_scores = self.ingestion_df["Correctness_Score"].tolist()
        total_correct_answers = sum(correctness_scores)
        total_answers = len(self.ingestion_df)

        correctness_rate = (total_correct_answers / total_answers) * 100

        self.scores_dict["correctness_rate"] = correctness_rate
        self._print("--------------------------------------")
        self._print(f"Correctness Rate: {correctness_rate}")
        self._print("--------------------------------------")
        print("[✔]")

    def write_scores(self):
        print("[*] Writing scores")

        with open(self.score_file, "w") as f_score:
            f_score.write(json.dumps(self.scores_dict, indent=4))

        self._print("\n\n\n\n\n")

        print("[✔]")

    def write_html(self, content):
        with open(self.html_file, 'a', encoding="utf-8") as f:
            f.write(content)

    def _print(self, content):
        print(content)
        self.write_html(content + "<br>")


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

    # Load ingestion result
    scoring.load_ingestion_result()

    # Write review to html
    scoring.write_reviews_to_html()

    # Compute rate of completeness
    scoring.compute_completeness_rate()

    # Compute rate of correctness
    scoring.compute_correctness_rate()

    # Write scores
    scoring.write_scores()

    # Stop timer
    scoring.stop_timer()

    # Show duration
    scoring.show_duration()

    print("\n----------------------------------------------")
    print("[✔] Scoring Program executed successfully!")
    print("----------------------------------------------\n\n")
