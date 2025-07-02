import argparse
from sklearn.manifold import TSNE
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_curve
import numpy as np

# Autosklearn
from evalml.automl import AutoMLSearch
import numpy as np
from sklearn.model_selection import train_test_split

from imblearn.over_sampling import SMOTE
from sklearn.metrics import precision_score, recall_score

def preprocess_data(df,
                    max_imbalance_scale=10,
                    max_samples_per_class=1000,
                    keep_classes_ratio=False,
                    min_samples_per_class=100):
    logs = ""
    
    # Get the features and labels
    X = df.drop(columns=[
        "SrcId",
        "StartTime",
        "LastTime",
        "SrcStartTime",
        "DstStartTime",
        "SrcLastTime",
        "DstLastTime",
        "SrcAddr",
        "DstAddr",
        "Sport",
        "Dport",
    ])


    # Preprocess the data
    X = X.fillna(0)
    X = X.dropna()

    # String to numbers using sklearn
    le = LabelEncoder()
    for col in X.columns:
        if X[col].dtype == "object" and col != "Label":
            # Ensure everything is string
            X[col] = X[col].astype(str)
            X[col] = le.fit_transform(X[col])

    X = X.drop_duplicates()
    # Get the first 1000 samples of each label

    # Get the occourrences of the less frequent label
    min_occ = X["Label"].value_counts().min()

    msg = "\n" + str(X["Label"].value_counts())
    print(msg)
    logs += msg


    # X = X.groupby("Label").head(min_occ*max_imbalance_scale)
    
    if not keep_classes_ratio:
        X = X.groupby("Label").head(max_samples_per_class)
    else:

        msg = f"\nEnsuring a maximum of {max_samples_per_class} samples per class (dropping random samples)..."
        print(msg)
        logs += msg

        # Find the raquired ratio to ensure a maximum of max_samples_per_class samples per class
        classes = X["Label"].unique()
        samples_per_class = X["Label"].value_counts()

        # Print original samples per class
        msg = "\nOriginal samples per class:"
        print(msg)
        logs += msg
        msg = "\n" + str(samples_per_class)

        samples_per_class = samples_per_class[samples_per_class > max_samples_per_class]
        samples_per_class = samples_per_class.to_dict()
        if len(samples_per_class) > 0:
            ratio = max([max_samples_per_class/samples_per_class[label] for label in samples_per_class])
            mspc = min([samples_per_class[label] for label in samples_per_class])

            ratio_options = [max_samples_per_class/per for per in samples_per_class.values()
                                if (1 - max_samples_per_class/per)*per > 0]
            
            if len(ratio_options) == 0:
                # If the ratio is too high, we will drop samples to ensure at least min_instances_per_class samples per class
                msg = f"\nCannot find drop ratio to ensure a maximum of {max_samples_per_class} samples per class. Skipping samples drop."
                print(msg)
                logs += msg
            else:
                ratio = min(ratio_options)
                msg = f"\nUsing ratio {ratio} to ensure a maximum of {max_samples_per_class} samples per class."
                print(msg)
                logs += msg
            
                for label in samples_per_class:
                    # Use ratio to keep the same ratio of samples for each class
                    X = X.drop(X[X["Label"] == label].sample(frac=1-ratio).index)

    # Count by label
    msg = "\n" + str(X["Label"].value_counts())
    print(msg)
    logs += msg

    # Identify and Drop classes with less than 2 sample
    classes_to_drop = X["Label"].value_counts()[X["Label"].value_counts() < 2].index
    X = X[~X["Label"].isin(classes_to_drop)]
    msg = f"\nDropping classes with less than 2 sample: {classes_to_drop}"
    print(msg)
    logs += msg

    X_features = X.copy()
    X_features = X_features.drop(columns=["Label"])

    # Normalize the data
    for col in X_features.columns:
        if col != "Label":
            X_features[col] = (X_features[col] - X_features[col].mean()) / X_features[col].std()
            # Replace nan values with 0
            X_features[col] = X_features[col].fillna(0)
    
    return logs, X, X_features

def tsne_analysis(df, dataset_path):
    logs = ""

    pp_logs, X, X_features = preprocess_data(df, max_samples_per_class=2000)
    logs += pp_logs

    # Perform t-SNE parallel
    tsne = TSNE(n_components=2, random_state=42, n_jobs=-1)
    X_features_embedded = tsne.fit_transform(X_features)

    # Add the t-SNE components to the dataframe
    X["tsne-2d-one"] = X_features_embedded[:, 0]
    X["tsne-2d-two"] = X_features_embedded[:, 1]

    # Save the new dataset
    X_features.to_csv(dataset_path.replace(".csv", "_tsne.csv"), index=False)
    
    # Assign colors to labels
    unique_labels = X["Label"].unique()
    num_classes = len(unique_labels)
    palette = sns.color_palette("viridis", num_classes)  # Get distinct colors
    label_color_map = {label: palette[i] for i, label in enumerate(unique_labels)}

    # Plot the t-SNE with correct colors
    plt.figure(figsize=(16, 10))
    for label, color in label_color_map.items():
        subset = X[X["Label"] == label]
        # plt.scatter(subset["tsne-2d-one"], subset["tsne-2d-two"], color=color, label=label, alpha=0.5)
        plt.scatter(subset["tsne-2d-one"], subset["tsne-2d-two"], label=label, alpha=0.5)

    # Set legend below the plot
    l = plt.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        fontsize=24,
        ncols=min(3, num_classes),
        frameon=False
    )

    # Points of the legend should be bigger
    for handle in l.legend_handles:
        handle.set_sizes([400])

    # Hide ticks and tick values
    plt.xticks([], [])
    plt.yticks([], [])
    plt.xlabel("")
    plt.ylabel("")

    # Remove lines around the plot
    plt.box(False)
    plt.tight_layout()

    # Save figure
    plt.savefig(dataset_path.replace(".csv", "_tsne.png"), dpi=300)

    return logs


def difficulty_analysis(df, dataset_path):
    logs = ""
    # Split train test
    

    replication_data_full = []
    replication_data_full_dict = {}
    for replication_id in range(10):
    # for replication_id in range(30):
        pp_logs, X, X_features = preprocess_data(df, max_samples_per_class=2000)
        full_X_train, X_test, full_y_train, y_test = train_test_split(X_features, X["Label"], test_size=0.5, random_state=42, shuffle=True)
        # for train_data_ratio in np.arange(0.1, 1.0, 0.05):
        
        # Convert labels to int
        le = LabelEncoder().fit(full_y_train)
        full_y_train = le.transform(full_y_train)
        y_test = le.transform(y_test)

        replication_data = []
        is_binary = len(set(full_y_train)) == 2
        problem_type = "binary" if is_binary else "multiclass"
        objective = "f1" if is_binary else "auto"
        for i in range(1, 10):
        # for i in range(1, 4):
            train_data_ratio = 0.001 + (2**i - 1)*0.001
            if len(full_X_train)*train_data_ratio < 2:
                continue
            
            X_train, _, y_train, _ = train_test_split(full_X_train, full_y_train, train_size=train_data_ratio, random_state=replication_id)

            allowed_min_class=3
            min_class = min([len(y_train[y_train == label]) for label in np.unique(y_train)])
            if len(set(y_train)) <= 1 or min_class < len(set(y_train)) or min_class < allowed_min_class:
                continue

            # If any class have less than min_samples_per_class samples, use imblearn for oversampling
            if min([len(y_train[y_train == label]) for label in np.unique(y_train)]) < 100:
                smote = SMOTE(sampling_strategy="minority", random_state=replication_id,
                              k_neighbors=min(allowed_min_class-1, 5))
                
                X_train, y_train = smote.fit_resample(X_train, y_train)
                
            # Train a classifier
            def log_error_callback(*args, **kwargs):
                return
            automl = AutoMLSearch(X_train=X_train, y_train=y_train, problem_type=problem_type, objective=objective, max_batches=1, optimize_thresholds=True, n_jobs=-1, verbose=False, error_callback=log_error_callback)
            # automl = AutoMLSearch(X_train=X_train, y_train=y_train, problem_type="binary", objective="f1", n_jobs=-1)
            automl.search()
            clf = automl.best_pipeline
            y_pred = clf.predict(X_test)
            f1score = f1_score(y_test, y_pred, average="macro")

            # AUC
            # Ensure y_test and y_pred are binary
            le = LabelEncoder().fit(y_test)
            y_test_b = le.transform(y_test)
            y_pred_b = le.transform(y_pred)
            fpr, tpr, thresholds = roc_curve(y_test_b, y_pred_b, pos_label=1)

            # Compute precision and recall

            precision = precision_score(y_test, y_pred, average="macro")
            recall = recall_score(y_test, y_pred, average="macro")

            auc = np.trapz(tpr, fpr)

            replication_data.append([train_data_ratio, auc])

            if not i in replication_data_full_dict:
                replication_data_full_dict[i] = []
            
            replication_data_full_dict[i].append([train_data_ratio, auc, f1score, precision, recall])

        if len(replication_data) > 0:
            replication_data_full.append(replication_data)
    
    data_ratio_list = []
    auc_mean_list = []
    auc_std_list = []
    f1_mean_list = []
    f1_std_list = []
    precision_mean_list = []
    precision_std_list = []
    recall_mean_list = []
    recall_std_list = []

    for i in sorted(list(replication_data_full_dict.keys())):
        replication_data_full_dict[i] = np.array(replication_data_full_dict[i])
        rep_data = np.mean(replication_data_full_dict[i], axis=0)
        data_ratio_list.append(rep_data[0])
        auc_mean_list.append(rep_data[1])
        auc_std_list.append(np.std(replication_data_full_dict[i], axis=0)[1])
        f1_mean_list.append(rep_data[2])
        f1_std_list.append(np.std(replication_data_full_dict[i], axis=0)[2])
        precision_mean_list.append(rep_data[3])
        precision_std_list.append(np.std(replication_data_full_dict[i], axis=0)[3])
        recall_mean_list.append(rep_data[4])
        recall_std_list.append(np.std(replication_data_full_dict[i], axis=0)[4])
    
    data_ratio_list = np.array(data_ratio_list)
    auc_mean_list = np.array(auc_mean_list)
    auc_std_list = np.array(auc_std_list)
    f1_mean_list = np.array(f1_mean_list)
    f1_std_list = np.array(f1_std_list)
    precision_mean_list = np.array(precision_mean_list)
    precision_std_list = np.array(precision_std_list)
    recall_mean_list = np.array(recall_mean_list)
    recall_std_list = np.array(recall_std_list)
        
    plt.figure(figsize=(10,10))
    plt.plot(data_ratio_list, auc_mean_list, label="AUC")
    plt.fill_between(data_ratio_list, auc_mean_list-auc_std_list, auc_mean_list+auc_std_list, alpha=0.3)
    plt.xlabel("Train data ratio")
    plt.ylabel("AUC")
    plt.legend()
    plt.savefig(dataset_path.replace(".csv", "difficulty_analysis.png"))

    # Also save mean and std to a csv file
    mean = np.concatenate((data_ratio_list.reshape(-1,1), auc_mean_list.reshape(-1,1), auc_std_list.reshape(-1,1), f1_mean_list.reshape(-1,1), f1_std_list.reshape(-1,1), precision_mean_list.reshape(-1,1), precision_std_list.reshape(-1,1), recall_mean_list.reshape(-1,1), recall_std_list.reshape(-1,1)), axis=1)
    mean_df = pd.DataFrame(mean, columns=["Train data ratio", "AUC", "STD AUC", "F1-Score", "STD F1-Score", "Precision", "STD Precision", "Recall", "STD Recall"])
    mean_df.to_csv(dataset_path.replace(".csv", "difficulty_analysis.csv"), index=False)
    
    msg = "Saved difficulty analysis to " + dataset_path.replace(".csv", "difficulty_analysis.csv")
    print(msg)
    logs += msg
    return logs

def classification_analysis(df, dataset_path):
    logs=""

    # Shuffle df
    df = df.sample(frac=1, random_state=42)
    
    scores = []
    cm_sum = None
    for rep_id in range(10):
        pp_logs, X, X_features = preprocess_data(df, max_samples_per_class=2000)
        # pp_logs, X, X_features = preprocess_data(df, max_samples_per_class=10000)

        # Run 10-fold cross validation using Random Forest
        # clf = RandomForestClassifier(random_state=rep_id)
        
        skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=rep_id)

        for train_index, test_index in skf.split(X_features, X["Label"]):
        # for test_index, train_index in skf.split(X_features, X["Label"]):
            X_train, X_test = X_features.iloc[train_index], X_features.iloc[test_index]
            y_train, y_test = X["Label"].iloc[train_index], X["Label"].iloc[test_index]

            automl = AutoMLSearch(X_train=X_train, y_train=y_train, problem_type="binary", objective="f1", max_batches=1, optimize_thresholds=True, n_jobs=-1)
            automl.search()
            clf = automl.best_pipeline

            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            f1score = f1_score(y_test, y_pred, average="macro")

            # AUC
            # Ensure y_test and y_pred are binary
            
            le = LabelEncoder().fit(y_test)
            y_test_b = le.transform(y_test)
            y_pred_b = le.transform(y_pred)
            
            fpr, tpr, thresholds = roc_curve(y_test_b, y_pred_b, pos_label=1)
            auc = np.trapz(tpr, fpr)
            # scores.append(f1score)
            scores.append(auc)

            cm = confusion_matrix(y_test, y_pred, labels=X["Label"].unique())
            if cm_sum is None:
                cm_sum = cm
            else:
                cm_sum += cm

    plt.figure(figsize=(10,10))
    sns.heatmap(cm_sum, annot=True, fmt="d", cmap="Blues", xticklabels=X["Label"].unique(), yticklabels=X["Label"].unique())
    plt.savefig(dataset_path.replace(".csv", "crossval_confusion_matrix_sum.png"))

    scores = pd.Series(scores)
    # scores = cross_val_score(clf, X_features, X["Label"], cv=10, scoring="f1_macro")

    msg = f"\n10-fold cross validation Random Forest F1-score: {scores.mean()}"
    print(msg)
    logs += msg

    # Split 50-50 train-test using Stratified Shuffle Split and save confusion matrix
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
    for train_index, test_index in sss.split(X_features, X["Label"]):
        X_train, X_test = X_features.iloc[train_index], X_features.iloc[test_index]
        y_train, y_test = X["Label"].iloc[train_index], X["Label"].iloc[test_index]

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    cm = confusion_matrix(y_test, y_pred, labels=X["Label"].unique())
    plt.figure(figsize=(10,10))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=X["Label"].unique(), yticklabels=X["Label"].unique())
    plt.savefig(dataset_path.replace(".csv", "_confusion_matrix.png"))

    # Classification report
    msg = "\nRandom Forest Classification report for Stratified 50-50 split:"
    print(msg)
    logs += msg
    msg = "\n" + str(classification_report(y_test, y_pred))
    print(msg)
    logs += msg

    return logs

def create_dataset_analysis(dataset_path, ignore_classes=[]):
    logs = ""
    df = pd.read_csv(dataset_path)

    # Remove ignored classes
    if len(ignore_classes) > 0:
        df = df[~df["Label"].isin(ignore_classes)]

    logs += tsne_analysis(df, dataset_path)

    # logs += classification_analysis(df, dataset_path)

    logs += difficulty_analysis(df, dataset_path)

    return logs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', type=str, required=True,
                        help='CSV labeled dataset to be used')

    parser.add_argument('-i', '--ignore', type=str, default="",
                        help='Comma separated list of classes to ignore')

    args = parser.parse_args()

    create_dataset_analysis(args.dataset, args.ignore.split(","))

if __name__ == "__main__":
    main()
