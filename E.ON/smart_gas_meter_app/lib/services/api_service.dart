//pt a face leg cu frontendul
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl = "http://192.168.56.1:8000";

  Future<Map<String, dynamic>> triggerReading() async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/upload-meter-photo'));

      if(response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception("Server error: ${response.statusCode}");
      }
    } catch (e) {
      return {"error": e.toString()};
    }
  }
}