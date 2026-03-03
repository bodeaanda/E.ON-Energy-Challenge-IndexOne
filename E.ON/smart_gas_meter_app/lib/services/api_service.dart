import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  // ATENȚIE: Dacă testezi pe emulator Android, folosește 10.0.2.2 în loc de localhost
  // Dacă testezi pe telefon fizic, folosește IP-ul laptopului (ex: 192.168.1.5)
  // În lib/services/api_service.dart
  // Pentru Chrome pe același laptop:
  final String baseUrl = "http://127.0.0.1:8000";

  // Takes the history table of the readings
  Future<List<dynamic>> fetchReadings() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/readings'));

      if (response.statusCode == 200) {
        final jsonResponse = jsonDecode(response.body);
        // Backend returns { "status": "success", "data": [...] }
        return jsonResponse['data']; 
      } else {
        throw Exception("Eroare server: ${response.statusCode}");
      }
    } catch (e) {
      print("Eroare la fetchReadings: $e");
      return []; // Returns empty list in case of errors
    }
  }
}