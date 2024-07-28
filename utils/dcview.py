import discord
import re



class greet_view(discord.ui.View):
  # View has a timeout of 180 seconds (3 minutes). The 2 lines of code below  timeout 
  def __init__(self) -> None:
      super().__init__(timeout=None)


  # First button - Just an Emoji, default color
  @discord.ui.button(custom_id = "emoji_button", emoji= '\U0001F606')
  async def say_hello(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.send_message(f'Hello!')


  # You can add up to 25 buttons to the same view, but make sure it's custom_id and function name are always different!
  # Second button - Label 'greet', green, no emoji
  @discord.ui.button(label='greet', custom_id = "greet_button", style = discord.ButtonStyle.blurple)
  async def greet_user(self, interaction: discord.Interaction, button: discord.ui.Button):
    user = interaction.user.id
    await interaction.response.send_message(f'Hello, <@{user}>, how are you doing today?')


  # Third button - Label 'say goodbye', red, has emoji
  @discord.ui.button(label='say goodbye', custom_id = "good_bye_button", emoji = '\U0001F601', style = discord.ButtonStyle.red)
  async def say_goodbye_to_user(self, interaction: discord.Interaction, button: discord.ui.Button):
    user = interaction.user.id
    await interaction.response.send_message(f'Good bye, <@{user}>, hope to see you soon!')


class LineButton(discord.ui.Button):
    def __init__(self, line_number: int, line_text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.line_number = line_number
        self.line_text = line_text

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("." + self.line_text)


class blog_view(discord.ui.View):
  # View has a timeout of 180 seconds (3 minutes). The 2 lines of code below  timeout 
  def __init__(self,answer="") -> None:
    super().__init__(timeout=None)
    self.answer = answer
    self.lines = [line for line in answer.split('\n') if re.match(r'^\d+\.', line)]
    print(self.lines)
    for i, line in enumerate(self.lines):
        line_text = re.sub('^\d+\. ', '', line)
        requestion = f'Describle the technical details of {line_text}.Make sure to include any important details, explanations, or examples that are relevant to each step. Please use the context below as ONLY reference and MUST NOT referencing other sources'
        self.add_item(LineButton(i, requestion, label=f'Step {i+1}', custom_id=f'button_{i}'))
        if i > 20:
            break



  # First button - Just an Emoji, default color
  @discord.ui.button(custom_id = "emoji_button", emoji= '\U0001F606')
  async def say_hello(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.send_message(f'summary the content!')


  # You can add up to 25 buttons to the same view, but make sure it's custom_id and function name are always different!
  # Second button - Label 'greet', green, no emoji
  @discord.ui.button(label='technical step', custom_id = "greet_button", style = discord.ButtonStyle.blurple)
  async def greet_user(self, interaction: discord.Interaction, button: discord.ui.Button):
    user = interaction.user.id
    await interaction.response.send_message(f'.Please provide a detailed, step-by-step breakdown of the technical process author did the work. Summarize the information into numbered steps to make it easy to understand and follow,Make sure to include any important details, explanations, or examples that are relevant to each step. Please use the context below as ONLY reference and MUST NOT referencing other sources')


  # Third button - Label 'say goodbye', red, has emoji
  @discord.ui.button(label="Tech question", custom_id = "good_bye_button", emoji = '\U0001F601', style = discord.ButtonStyle.red)
  async def say_goodbye_to_user(self, interaction: discord.Interaction, button: discord.ui.Button):
    user = interaction.user.id
    await interaction.response.send_message(f'.Please provide the technical detailed of the vulnerability')
    
