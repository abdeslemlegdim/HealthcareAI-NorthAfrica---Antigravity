from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=pcsk_2qxL2b_T8zrGbeMNcbAu7yQcgYAWRVf7sTNJJ7pRQm31ZjA5GG4burKqXgugYHPyPB3uJE )

# Create an index if it doesn't exist
if "quickstart" not in pc.list_indexes().names():
    pc.create_index(
        name="quickstart",
        dimension=1536,  # Adjust based on your embedding model
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

# Connect to the existing index
index = pc.Index("quickstart")
