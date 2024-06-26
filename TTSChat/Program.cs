using Raylib_cs;
public class Program
{
    public static void Main(string[] args)
    {
        Raylib.InitWindow(800, 450, "TTS Chat");
        Raylib.InitAudioDevice();
        Raylib.SetTargetFPS(30);
        while (!Raylib.WindowShouldClose())
        {
            Raylib.BeginDrawing();
            Raylib.ClearBackground(Color.White);
            Raylib.DrawText("TTS Chat", 10, 10, 20, Color.Black);

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
