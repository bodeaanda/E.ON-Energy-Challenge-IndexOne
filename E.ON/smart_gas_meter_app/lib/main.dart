import 'package:flutter/material.dart';
import 'services/api_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Gas Meter',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Istoric Consum Gaz'),
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
  final ApiService _apiService = ApiService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() {}); 
            },
          )
        ],
      ),
      body: Center(
        child: FutureBuilder<List<dynamic>>(
          future: _apiService.fetchReadings(),
          builder: (context, snapshot) {
            
            // 1. Încărcare
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 10),
                  Text("Se încarcă datele..."),
                ],
              );
            } 
            
            // 2. Eroare
            else if (snapshot.hasError) {
              return Padding(
                padding: const EdgeInsets.all(16.0),
                child: Text(
                  "Eroare: ${snapshot.error}\n\nVerifică dacă serverul Python rulează și IP-ul e corect în api_service.dart",
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.red),
                ),
              );
            } 
            
            // 3. Avem date
            else if (snapshot.hasData && snapshot.data!.isNotEmpty) {
              var latest = snapshot.data![0];
              
              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(height: 20),
                  const Text(
                    'Ultima valoare citită:',
                    style: TextStyle(fontSize: 18),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    '${latest['value']} m³', 
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Colors.deepPurple,
                        ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'Data: ${latest['date']}',
                    style: const TextStyle(color: Colors.grey, fontSize: 14),
                  ),
                  const SizedBox(height: 30),
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.all(8.0),
                    child: Text("Istoric recent:", style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  
                  // Lista cu istoric
                  Expanded(
                    child: ListView.builder(
                      itemCount: snapshot.data!.length,
                      itemBuilder: (context, index) {
                        var item = snapshot.data![index];
                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          child: ListTile(
                            leading: const Icon(Icons.speed, color: Colors.deepPurple),
                            title: Text("${item['value']} m³", style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text(item['date']),
                          ),
                        );
                      },
                    ),
                  )
                ],
              );
            } 
            
            // 4. Listă goală
            else {
              return const Text("Nu există citiri în baza de date.");
            }
          },
        ),
      ),
    );
  }
}