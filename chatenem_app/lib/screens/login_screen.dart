import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter/foundation.dart';
import 'home_screen.dart';

class LoginScreen extends StatelessWidget {
  final VoidCallback onToggleTheme;
  final ThemeMode themeMode;

  const LoginScreen({
    super.key,
    required this.onToggleTheme,
    required this.themeMode,
  });

Future<void> loginAsGuest(BuildContext context) async {
  Navigator.pushReplacement(
    context,
    MaterialPageRoute(
      builder: (_) => HomeScreen(
        onToggleTheme: onToggleTheme,
        themeMode: themeMode,
      ),
    ),
  );
}


  Future<void> loginWithGoogle(BuildContext context) async {
    await Supabase.instance.client.auth.signInWithOAuth(
      OAuthProvider.google,
      scopes: 'openid email profile',
      redirectTo: kIsWeb ? null : 'io.supabase.flutter://login-callback',
    );
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: Stack(
        children: [
          // 🌈 FUNDO + CONTEÚDO
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: isDark
                    ? [
                        Colors.deepPurple.shade900,
                        Colors.indigo.shade900,
                        Colors.blueGrey.shade900,
                      ]
                    : [
                        Colors.purple.shade50,
                        Colors.blue.shade50,
                        Colors.white,
                      ],
              ),
            ),
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // 🔮 LOGO ANIMADA
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 800),
                      curve: Curves.fastOutSlowIn,
                      width: size.width * 0.3,
                      height: size.width * 0.3,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: isDark
                              ? [Colors.purpleAccent, Colors.blueAccent]
                              : [Colors.purple, Colors.blue],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.purple.withOpacity(0.3),
                            blurRadius: 20,
                            spreadRadius: 5,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.chat_bubble_outline,
                        color: Colors.white,
                        size: 50,
                      ),
                    ),

                    const SizedBox(height: 32),

                    // 🧠 TÍTULO COM GRADIENTE
                    ShaderMask(
                      shaderCallback: (bounds) => LinearGradient(
                        colors: isDark
                            ? [Colors.purpleAccent, Colors.blueAccent]
                            : [Colors.purple, Colors.blue],
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ).createShader(bounds),
                      child: const Text(
                        'ChatENEM',
                        style: TextStyle(
                          fontSize: 42,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),

                    const SizedBox(height: 8),

                    // 📝 SUBTÍTULO
                    Text(
                      'Prepare-se para o ENEM com IA',
                      style: TextStyle(
                        fontSize: 16,
                        color:
                            isDark ? Colors.grey.shade300 : Colors.grey.shade700,
                      ),
                    ),

                    const SizedBox(height: 48),

                    // 💳 CARD DE LOGIN
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 600),
                      curve: Curves.easeInOut,
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: isDark
                            ? Colors.grey.shade900.withOpacity(0.8)
                            : Colors.white.withOpacity(0.9),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          // 🔵 BOTÃO GOOGLE
                          ElevatedButton(
                            onPressed: () => loginWithGoogle(context),
                            style: ElevatedButton.styleFrom(
                              backgroundColor:
                                  isDark ? Colors.grey.shade800 : Colors.white,
                              foregroundColor:
                                  isDark ? Colors.white : Colors.grey.shade800,
                              minimumSize: const Size(double.infinity, 56),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                                side: BorderSide(
                                  color: isDark
                                      ? Colors.grey.shade700
                                      : Colors.grey.shade300,
                                ),
                              ),
                              elevation: 0,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Image.asset(
                                  'assets/images/google_logo.png',
                                  height: 24,
                                  width: 24,
                                  errorBuilder: (context, error, stackTrace) =>
                                      const Icon(Icons.g_mobiledata),
                                ),
                                const SizedBox(width: 12),
                                const Text(
                                  'Entrar com Google',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 20),

                          // ➖ DIVISOR
                          Row(
                            children: [
                              Expanded(
                                child: Divider(
                                  color: isDark
                                      ? Colors.grey.shade700
                                      : Colors.grey.shade300,
                                ),
                              ),
                              Padding(
                                padding:
                                    const EdgeInsets.symmetric(horizontal: 16),
                                child: Text(
                                  'ou',
                                  style: TextStyle(
                                    color: isDark
                                        ? Colors.grey.shade400
                                        : Colors.grey.shade600,
                                  ),
                                ),
                              ),
                              Expanded(
                                child: Divider(
                                  color: isDark
                                      ? Colors.grey.shade700
                                      : Colors.grey.shade300,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 20),

                          // 👤 BOTÃO CONVIDADO
                          OutlinedButton(
                            onPressed: () => loginAsGuest(context),
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(double.infinity, 56),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              side: BorderSide(
                                color:
                                    isDark ? Colors.purpleAccent : Colors.purple,
                                width: 2,
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.person_outline,
                                  color:
                                      isDark ? Colors.purpleAccent : Colors.purple,
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  'Entrar como Convidado',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                    color: isDark
                                        ? Colors.purpleAccent
                                        : Colors.purple,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 32),

                    // 📄 TERMOS DE USO
                    Text(
                      'Ao continuar, você concorda com nossos Termos de Uso\n e Política de Privacidade',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        color:
                            isDark ? Colors.grey.shade500 : Colors.grey.shade600,
                      ),
                    ),

                    const SizedBox(height: 40),

                    // 🌊 ONDAS DECORATIVAS (apenas modo claro)
                    if (!isDark)
                      SizedBox(
                        height: 100,
                        child: Stack(
                          alignment: Alignment.bottomCenter,
                          children: [
                            CustomPaint(
                              size: Size(size.width, 80),
                              painter: WavePainter(),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),

          // 🌙☀️ BOTÃO DE TEMA (FLOATING)
          SafeArea(
            child: Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.only(right: 12),
                child: IconButton(
                  style: IconButton.styleFrom(
                    backgroundColor: isDark ? Colors.black26 : Colors.white,
                  ),
                  icon: Icon(
                    themeMode == ThemeMode.dark
                        ? Icons.light_mode
                        : Icons.dark_mode,
                  ),
                  onPressed: onToggleTheme,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// 🎨 PAINTER PARA ONDAS DECORATIVAS
class WavePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.purple.withOpacity(0.1)
      ..style = PaintingStyle.fill;

    final path = Path();
    path.moveTo(0, size.height * 0.7);
    path.quadraticBezierTo(
      size.width * 0.25,
      size.height * 0.6,
      size.width * 0.5,
      size.height * 0.7,
    );
    path.quadraticBezierTo(
      size.width * 0.75,
      size.height * 0.8,
      size.width,
      size.height * 0.7,
    );
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();

    canvas.drawPath(path, paint);

    // Segunda onda
    paint.color = Colors.blue.withOpacity(0.1);
    path.reset();
    path.moveTo(0, size.height * 0.8);
    path.quadraticBezierTo(
      size.width * 0.3,
      size.height * 0.9,
      size.width * 0.6,
      size.height * 0.8,
    );
    path.quadraticBezierTo(
      size.width * 0.8,
      size.height * 0.7,
      size.width,
      size.height * 0.8,
    );
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}