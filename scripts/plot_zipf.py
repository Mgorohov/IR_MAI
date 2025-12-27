import matplotlib.pyplot as plt
import pandas as pd
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
zipf_csv_path = os.path.join(project_root, "data", "zipf.csv")
output_image_path = os.path.join(project_root, "images", "zipf.png")

os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

def plot_zipf_law():
    if not os.path.exists(zipf_csv_path):
        print(f"Error: {zipf_csv_path} not found. Please run build_index.py first.")
        return

    df = pd.read_csv(zipf_csv_path)

    if df.empty:
        print("Error: Zipf data is empty. Cannot plot.")
        return

    plt.figure(figsize=(10, 6))
    plt.loglog(df['rank'], df['freq'], label='corpus')
    plt.loglog(df['rank'], df['zipf_approx'], label='Zipf C/r')

    plt.title("Zipf law")
    plt.xlabel("rank (log)")
    plt.ylabel("frequency (log)")
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)

    plt.savefig(output_image_path)
    print(f"Zipf's law plot saved to {output_image_path}")

if __name__ == "__main__":
    plot_zipf_law()

