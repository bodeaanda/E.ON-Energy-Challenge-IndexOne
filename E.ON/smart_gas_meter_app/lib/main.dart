import 'package:flutter/material.dart';
import 'package:http/http.dart' as http; // Importăm librăria pentru request-uri
import 'dart:convert'; // Importăm pentru a decoda răspunsul JSON de la server

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Gas Meter',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Control Contor Gaz'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  // Schimbăm în double pentru că citirea contorului poate avea zecimale
  double _lastReading = 0.0; 
  bool _isRequesting = false; // Status pentru a arăta că așteptăm răspunsul

  // Funcția principală care "vorbește" cu backend-ul tău
  Future<void> _requestGasReading() async {
    setState(() {
      _isRequesting = true;
    });

    // ATENȚIE: Dacă testezi în browser (Chrome) pe același PC, lasă localhost.
    // Dacă testezi pe un telefon real, pune IP-ul calculatorului tău (ex: 192.168.1.15)
    final url = Uri.parse('http://localhost:8000/upload-meter-photo');

    try {
      print("Trimit solicitare citire către server...");
      final response = await http.post(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        setState(() {
          // Luăm valoarea 'reading' din JSON-ul trimis de Python
          _lastReading = (data['reading'] as num).toDouble();
          _isRequesting = false;
        });
        
        print("Citire reușită: $_lastReading");
      } else {
        print("Eroare server: ${response.statusCode}");
        _showErrorSnackBar("Eroare la server: ${response.statusCode}");
      }
    } catch (e) {
      print("Eroare conexiune: $e");
      _showErrorSnackBar("Nu pot contacta serverul. Verifică dacă Python rulează!");
    } finally {
      setState(() {
        _isRequesting = false;
      });
    }
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Ultima valoare citită de pe contor:',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 10),
            // Afișăm un cerc de încărcare dacă așteptăm răspunsul
            _isRequesting 
              ? const CircularProgressIndicator()
              : Text(
                  '$_lastReading m³',
                  style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.deepPurple,
                  ),
                ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isRequesting ? null : _requestGasReading,
        tooltip: 'Solicită Citire',
        label: const Text("Citește Contorul"),
        icon: const Icon(Icons.camera_alt),
      ),
    );
  }
}