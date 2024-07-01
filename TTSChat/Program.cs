using Raylib_cs;
using System;
using System.Diagnostics;
using System.IO;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

public class Program
{
    [DllImport("user32.dll")]
    static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    const uint SWP_NOSIZE = 0x0001;
    const uint SWP_NOMOVE = 0x0002;

    public static Button chatButton = new Button("TTS Generator", 10, 40, 200, 50, () =>
    {
        StartChatAudioGenerator();
        chatButton.active = false;
    });

    public static Button twitchPlaysButton = new Button("Twitch Plays", 10, 100, 200, 50, () =>
    {
        StartTwitchPlays();
        twitchPlaysButton.active = false;
    });

    public static unsafe void Main(string[] args)
    {
        Raylib.InitWindow(250, 200, "TTS Chat");
        Raylib.InitAudioDevice();
        Raylib.SetTargetFPS(60);
        Raylib.SetExitKey(0); // disable exit key

        // Set the window to always on top
        IntPtr windowHandle = (IntPtr)Raylib.GetWindowHandle();
        SetWindowPos(windowHandle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);

        while (!Raylib.WindowShouldClose())
        {
            float deltaTime = Raylib.GetFrameTime();
            chatButton?.Update(deltaTime);
            twitchPlaysButton?.Update(deltaTime);

            Raylib.BeginDrawing();
            Raylib.ClearBackground(Color.RayWhite);
            Raylib.DrawText("TTS Chat", 10, 10, 20, Color.Black);
            chatButton?.Draw();
            twitchPlaysButton?.Draw();

            // Check for and play audio
            if (File.Exists("output.wav"))
            {
                Sound sound = Raylib.LoadSound("output.wav");
                if (sound.Stream.Buffer != IntPtr.Zero)
                {
                    Raylib.PlaySound(sound);
                    File.Delete("output.wav");
                }
                else
                {
                    Raylib.TraceLog(TraceLogLevel.Error, "Failed to load sound");
                }
            }

            Raylib.EndDrawing();
        }

        Raylib.CloseWindow();
    }

    private static async void StartChatAudioGenerator()
    {
        await Task.Run(() =>
        {
            var process = new Process();
            process.StartInfo.FileName = "cmd.exe";
            process.StartInfo.Arguments = "/c C:/Users/ari/miniconda3/envs/coquitts/python.exe ChatAudioGenerator.py";
            process.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;  // Optionally hide the command window
            process.Start();
            process.WaitForExit(); // Wait for the process to exit
            chatButton.active = true; // Re-enable the button
        });
    }

    private static async void StartTwitchPlays()
    {
        await Task.Run(() =>
        {
            var process = new Process();
            process.StartInfo.FileName = "cmd.exe";
            process.StartInfo.Arguments = "/c start cmd.exe /k C:/Users/ari/miniconda3/envs/coquitts/python.exe TwitchPlays.py";
            process.StartInfo.WindowStyle = ProcessWindowStyle.Normal;  // Optionally show the command window
            process.Start();
            process.WaitForExit(); // Wait for the process to exit
            twitchPlaysButton.active = true; // Re-enable the button
        });
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
        // Check if mouse left-clicked
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
