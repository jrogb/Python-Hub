import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def find_forbidden_characters_and_long_paths(directory, output_file_path):
    """
    Scans a directory for files and folders containing forbidden characters or exceeding the maximum path length,
    and writes the findings to a specified output file.

    Args:
        directory (str): The path to the directory to scan.
        output_file_path (str): The full path where the output text file will be created.

    Returns:
        None. Writes the paths of files/folders with forbidden characters or long paths to a file.
    """

    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*','@']
    # Windows maximum path length (MAX_PATH) is 260 characters, including the null terminator.
    # We typically check against 259 to be safe for filenames/directories within that limit.
    max_path_length = 260
    found_issues = False

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Scan Report for Directory: {directory}\n")
            f.write("-------------------------------------------------------------------\n\n")
            print(f"Scanning directory: {directory}")
            print(f"Results will be saved to: {output_file_path}\n")

            for root, dirs, files in os.walk(directory):
                # Check directory names
                for d_name in dirs:
                    full_dir_path = os.path.join(root, d_name)
                    
                    # Check for forbidden characters
                    has_forbidden_char_in_name = False
                    for char in forbidden_chars:
                        if char in d_name:
                            f.write(f"Issue: Forbidden character '{char}' found in directory name: {full_dir_path}\n")
                            print(f"  Found issue: Directory '{d_name}' contains forbidden char '{char}'")
                            found_issues = True
                            has_forbidden_char_in_name = True
                            break  # Move to the next directory name once a forbidden char is found

                    # Check for path length (even if it has forbidden chars, it might also be too long)
                    if len(full_dir_path) >= max_path_length: # Using >= to include the 260th character
                        f.write(f"Issue: Directory path too long ({len(full_dir_path)} chars > {max_path_length-1} allowed): {full_dir_path}\n")
                        print(f"  Found issue: Directory path '{full_dir_path}' is too long ({len(full_dir_path)} chars)")
                        found_issues = True

                # Check file names
                for f_name in files:
                    full_file_path = os.path.join(root, f_name)

                    # Check for forbidden characters
                    has_forbidden_char_in_name = False
                    for char in forbidden_chars:
                        if char in f_name:
                            f.write(f"Issue: Forbidden character '{char}' found in file name: {full_file_path}\n")
                            print(f"  Found issue: File '{f_name}' contains forbidden char '{char}'")
                            found_issues = True
                            has_forbidden_char_in_name = True
                            break  # Move to the next file name once a forbidden char is found
                    
                    # Check for path length
                    if len(full_file_path) >= max_path_length: # Using >= to include the 260th character
                        f.write(f"Issue: File path too long ({len(full_file_path)} chars > {max_path_length-1} allowed): {full_file_path}\n")
                        print(f"  Found issue: File path '{full_file_path}' is too long ({len(full_file_path)} chars)")
                        found_issues = True

            if not found_issues:
                f.write("No files or folders with forbidden characters or paths exceeding the maximum length found.\n")
                print("\nNo files or folders with forbidden characters or paths exceeding the maximum length found.")

            print(f"\nScan complete. Check '{output_file_path}' for detailed results.")
            messagebox.showinfo("Scan Complete", f"Scan finished successfully!\nResults saved to:\n{output_file_path}")

    except Exception as e:
        error_message = f"An unexpected error occurred during scanning or writing the report: {e}"
        print(f"Error: {error_message}")
        messagebox.showerror("Error", error_message)

if __name__ == "__main__":
    # Hide the main Tkinter window (the small empty window that appears)
    root = tk.Tk()
    root.withdraw()

    # Determine the user's desktop path based on the operating system
    if sys.platform == "win32":
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
    elif sys.platform == "darwin":  # macOS
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    else:  # Linux/Unix
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        # Fallback for some Linux environments where Desktop might not be capitalized
        if not os.path.exists(desktop_path):
            desktop_path = os.path.join(os.path.expanduser("~"), "desktop") # common lowercase desktop for some Linux distributions

    output_filename = "Windows_Path_Scan_Report.txt"
    output_full_path = os.path.join(desktop_path, output_filename)

    # Open directory selection dialog
    print("Please select the directory to scan...")
    target_directory = filedialog.askdirectory(title="Select Directory to Scan for Windows Compatibility Issues")

    if not target_directory:
        messagebox.showwarning("No Directory Selected", "No directory was selected. Exiting.")
        sys.exit(0)  # Exit gracefully if no directory is chosen
    elif not os.path.isdir(target_directory):
        messagebox.showerror("Invalid Directory", f"The selected path:\n'{target_directory}'\nis not a valid directory. Please try again.")
        sys.exit(1)  # Exit with an error code

    find_forbidden_characters_and_long_paths(target_directory, output_full_path)