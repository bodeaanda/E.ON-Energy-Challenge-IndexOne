import 'package:flutter/material.dart';
import '../services/api_service.dart';

class GasProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  List<dynamic> _readings = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<dynamic> get readings => _readings;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchReadings() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners(); 

    try {
      _readings = await _apiService.fetchReadings();
    } catch (e) {
      _errorMessage = "A connection problem has occured: $e";
      print(e);
    }

    _isLoading = false;
    notifyListeners(); 
  }
}