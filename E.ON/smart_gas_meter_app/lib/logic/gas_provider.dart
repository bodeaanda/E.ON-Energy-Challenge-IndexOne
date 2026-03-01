//retine val citita si anunta interfata cand datele se modifica

import 'package:flutter/material.dart';
import '../services/api_service.dart';

class GasProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  double? _lastReading;
  bool _isLoading = false;
  String? _errorMessage;

  //ca UI sa citeasca datele
  double? get lastReading => _lastReading;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchNewReading() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners(); 

    try {
      final data = await _apiService.triggerReading();
      if (data.containsKey('error')) {
        _errorMessage = data['error'];
      } else {
        _lastReading = data['reading'];
      }
    } catch (e) {
      _errorMessage = "A aparut o problema de conexiune.";
    }

    _isLoading = false;
    notifyListeners(); 
  }
}