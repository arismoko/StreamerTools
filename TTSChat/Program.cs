using Raylib_cs;
using System.Numerics;
public class Program
{
    public static Button chatButton = new Button("TTS Generator", 10, 40, 200, 50, () =>
        {
            System.Diagnostics.Process.Start("cmd.exe", "/c C:/Users/ari/miniconda3/envs/coquitts/python.exe ChatAudioGenerator.py");

            if (chatButton != null) chatButton.active = false;
        });
    public static Button twitchPlaysButton = new Button("Twitch Plays", 10, 100, 200, 50, () =>
        {
            System.Diagnostics.Process.Start("cmd.exe", "/c C:/Users/ari/miniconda3/envs/coquitts/python.exe TwitchPlays.py");
            if (twitchPlaysButton != null) twitchPlaysButton.active = false;
        });
    public static void Main(string[] args)
    {
        Raylib.InitWindow(800, 450, "TTS Chat");
        Raylib.InitAudioDevice();
        Raylib.SetTargetFPS(60);
        Raylib.SetExitKey(0); // disable exit key
        while (!Raylib.WindowShouldClose())
        {
            float deltaTime = Raylib.GetFrameTime();
            chatButton?.Update(deltaTime);
            chatButton?.Update(deltaTime);
            twitchPlaysButton?.Update(deltaTime);
            Raylib.BeginDrawing();
            Raylib.ClearBackground(Color.White);
            Raylib.DrawText("TTS Chat", 10, 10, 20, Color.Black);
            chatButton?.Draw();
            twitchPlaysButton?.Draw();
            //check for file at output.wav and play it
            if (File.Exists("output.wav"))
            {
                Sound sound = Raylib.LoadSound("output.wav");
                if (sound.Stream.Buffer != IntPtr.Zero)
                {
                    Raylib.PlaySound(sound);
                    File.Delete("output.wav");
                }
                else Raylib.TraceLog(TraceLogLevel.Error, "Failed to load sound");
            }



            Raylib.EndDrawing();
        }
        Raylib.CloseWindow();
    }
}
public class Button
{
    public string Text { get; }
    public int X { get; }
    public int Y { get; }
    public int Width { get; }
    public int Height { get; }

    public bool active = true;

    private bool isEnabled = true;
    private readonly Action callback;
    private readonly float disableTime = 1f; // in seconds
    private float elapsedTime = 0f;

    public Button(string text, int x, int y, int width, int height, Action callback)
    {
        Text = text;
        X = x;
        Y = y;
        Width = width;
        Height = height;
        this.callback = callback;
    }

    public void Update(float deltaTime)
    {
        if (!active) return;
        if (!isEnabled)
        {
            elapsedTime += deltaTime;
            if (elapsedTime >= disableTime)
            {
                isEnabled = true;
                elapsedTime = 0f;
            }
        }
        //check if mouse is left left clicked
        if (Raylib.IsMouseButtonPressed(MouseButton.Left))
        {
            Vector2 mousePos = Raylib.GetMousePosition();
            if (mousePos.X >= X && mousePos.X <= X + Width && mousePos.Y >= Y && mousePos.Y <= Y + Height)
            {
                OnClick();
            }
        }

    }

    public void Draw()
    {
        if (!active) return;
        Raylib.DrawRectangle(X, Y, Width, Height, isEnabled ? Color.LightGray : Color.Gray);
        Raylib.DrawText(Text, X + 10, Y + 10, 20, Color.Black);
    }

    public void OnClick()
    {
        if (isEnabled)
        {
            callback?.Invoke();
            isEnabled = false;
        }
    }
}