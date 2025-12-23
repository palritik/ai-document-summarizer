# from summarizer import chunk_text, summarize_chunk
# from keypoints import extract_key_points
# from pdf_reader import read_pdf

# print("📄 AI Document Summary Converter")

# file_type = input("Enter file type (txt/pdf): ").lower()

# if file_type == "txt":
#     path = input("Enter text file path: ")
#     with open(path, "r", encoding="utf-8") as file:
#         text = file.read()

# elif file_type == "pdf":
#     path = input("Enter PDF file path: ")
#     text = read_pdf(path)

# else:
#     print("❌ Invalid file type")
#     exit()

# chunks = chunk_text(text)
# summaries = [summarize_chunk(c) for c in chunks[:5]]

# print("\n🔹 SUMMARY:")
# print(" ".join(summaries))

# print("\n🔹 IMPORTANT POINTS:")
# points = extract_key_points(text)
# for i, p in enumerate(points, 1):
#     print(f"{i}. {p}")
