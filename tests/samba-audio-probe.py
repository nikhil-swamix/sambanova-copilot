from openai import OpenAI
file = open("./harvard.wav",'rb')
client = OpenAI(base_url="https://api.sambanova.ai/v1/audio/transcriptions", api_key="cecede0e-9ccd-44cd-a9fa-dbed784a2f0e")

transcript = client.audio.transcriptions.create(
  file=file,
  model="whisper-large-v3",
  # response_format="verbose_json",
  # timestamp_granularities=["word"]
)

print(transcript)
