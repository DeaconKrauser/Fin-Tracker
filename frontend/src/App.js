import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create AuthContext
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Create ThemeContext
const ThemeContext = createContext();

const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// ThemeProvider Component
const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    localStorage.setItem('theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// AuthProvider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
    }
    setLoading(false);
  }, []);

  const login = (tokenData) => {
    setToken(tokenData.access_token);
    setUser(tokenData.user);
    localStorage.setItem('token', tokenData.access_token);
    localStorage.setItem('user', JSON.stringify(tokenData.user));
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');
  const { login } = useAuth();
  const { theme } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const endpoint = isLogin ? '/login' : '/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      login(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer login/registro');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-purple-900 dark:to-indigo-900 flex items-center justify-center p-4 transition-colors duration-300">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-xl w-full max-w-md transition-colors duration-300">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2 transition-colors duration-300">
            💰 Finanças Tracker
          </h1>
          <p className="text-gray-600 dark:text-gray-300 transition-colors duration-300">
            {isLogin ? 'Entre na sua conta' : 'Crie sua conta'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded mb-4 transition-colors duration-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 transition-colors duration-300">
                Nome
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-300"
                required={!isLogin}
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 transition-colors duration-300">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-300"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 transition-colors duration-300">
              Senha
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-300"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 dark:bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 dark:hover:bg-purple-700 transition duration-200"
          >
            {isLogin ? 'Entrar' : 'Registrar'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300 text-sm transition-colors duration-300"
          >
            {isLogin ? 'Não tem conta? Registre-se' : 'Já tem conta? Faça login'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Profile Component
const Profile = ({ onBack }) => {
  const { user, updateUser } = useAuth();
  const { theme } = useTheme();
  const [formData, setFormData] = useState({
    name: user?.name || '',
    current_password: '',
    new_password: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      const updateData = { name: formData.name };
      if (formData.current_password && formData.new_password) {
        updateData.current_password = formData.current_password;
        updateData.new_password = formData.new_password;
      }

      const response = await axios.put(`${API}/profile`, updateData);
      updateUser(response.data);
      setMessage('Perfil atualizado com sucesso!');
      setFormData(prev => ({ ...prev, current_password: '', new_password: '' }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao atualizar perfil');
    }
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          await axios.post(`${API}/profile/avatar`, {
            avatar: event.target.result
          });
          setMessage('Avatar atualizado com sucesso!');
          // Update user in context (you might want to refetch user data)
        } catch (err) {
          setError('Erro ao atualizar avatar');
        }
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 transition-colors duration-300">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Perfil do Usuário</h2>
          <button
            onClick={onBack}
            className="text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300 text-sm"
          >
            ← Voltar ao Dashboard
          </button>
        </div>

        <div className="mb-6 text-center">
          <div className="relative inline-block">
            <div className="w-24 h-24 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center text-2xl font-semibold text-gray-600 dark:text-gray-300 mb-4">
              {user?.avatar ? (
                <img src={user.avatar} alt="Avatar" className="w-24 h-24 rounded-full object-cover" />
              ) : (
                user?.name?.charAt(0)?.toUpperCase() || '👤'
              )}
            </div>
            <label className="absolute bottom-0 right-0 bg-blue-600 dark:bg-purple-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700 dark:hover:bg-purple-700 transition-colors duration-200">
              📷
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {message && (
          <div className="bg-green-100 dark:bg-green-900/30 border border-green-400 dark:border-green-600 text-green-700 dark:text-green-300 px-4 py-3 rounded mb-4">
            {message}
          </div>
        )}

        {error && (
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nome
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email (não pode ser alterado)
            </label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400"
            />
          </div>

          <div className="border-t dark:border-gray-600 pt-4 mt-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Alterar Senha</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Senha Atual
              </label>
              <input
                type="password"
                value={formData.current_password}
                onChange={(e) => setFormData({...formData, current_password: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nova Senha
              </label>
              <input
                type="password"
                value={formData.new_password}
                onChange={(e) => setFormData({...formData, new_password: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 dark:bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 dark:hover:bg-purple-700 transition duration-200"
          >
            Atualizar Perfil
          </button>
        </form>
      </div>
    </div>
  );
};

// User Management Component
const UserManagement = ({ onBack }) => {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (err) {
      console.error('Erro ao carregar usuários:', err);
    }
    setLoading(false);
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/users/${userId}/role`, { role: newRole });
      fetchUsers(); // Refresh the list
    } catch (err) {
      console.error('Erro ao atualizar role:', err);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Acesso Negado</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">Apenas administradores podem acessar esta página.</p>
          <button
            onClick={onBack}
            className="text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300"
          >
            ← Voltar ao Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow transition-colors duration-300">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-600 flex justify-between items-center">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Gestão de Usuários</h2>
          <button
            onClick={onBack}
            className="text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300 text-sm"
          >
            ← Voltar ao Dashboard
          </button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-purple-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-300">Carregando usuários...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-600">
                    <th className="text-left py-3 text-gray-900 dark:text-white">Nome</th>
                    <th className="text-left py-3 text-gray-900 dark:text-white">Email</th>
                    <th className="text-left py-3 text-gray-900 dark:text-white">Role</th>
                    <th className="text-left py-3 text-gray-900 dark:text-white">Transações</th>
                    <th className="text-left py-3 text-gray-900 dark:text-white">Criado em</th>
                    <th className="text-left py-3 text-gray-900 dark:text-white">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-b border-gray-100 dark:border-gray-700">
                      <td className="py-3 text-gray-900 dark:text-white">{u.name}</td>
                      <td className="py-3 text-gray-600 dark:text-gray-300">{u.email}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          u.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' 
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 text-gray-600 dark:text-gray-300">{u.transactions_count}</td>
                      <td className="py-3 text-gray-600 dark:text-gray-300">
                        {new Date(u.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="py-3">
                        <select
                          value={u.role}
                          onChange={(e) => updateUserRole(u.id, e.target.value)}
                          className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          disabled={u.id === user.id}
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categorySummary, setCategorySummary] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'profile', 'users'
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    type: 'expense',
    category_id: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, transactionsRes, categoriesRes, categorySummaryRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/transactions`),
        axios.get(`${API}/categories`),
        axios.get(`${API}/dashboard/categories`)
      ]);

      setSummary(summaryRes.data);
      setTransactions(transactionsRes.data);
      setCategories(categoriesRes.data);
      setCategorySummary(categorySummaryRes.data);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount)
      };
      
      await axios.post(`${API}/transactions`, payload);
      setFormData({
        description: '',
        amount: '',
        type: 'expense',
        category_id: '',
        date: new Date().toISOString().split('T')[0]
      });
      setShowForm(false);
      fetchData();
    } catch (err) {
      console.error('Erro ao criar transação:', err);
    }
  };

  const deleteTransaction = async (id) => {
    try {
      await axios.delete(`${API}/transactions/${id}`);
      fetchData();
    } catch (err) {
      console.error('Erro ao deletar transação:', err);
    }
  };

  const filteredCategories = categories.filter(cat => cat.type === formData.type);

  // Pie Chart Data
  const pieChartData = {
    labels: categorySummary.map(cat => cat.category_name),
    datasets: [
      {
        data: categorySummary.map(cat => cat.total_amount),
        backgroundColor: categorySummary.map(cat => cat.category_color),
        borderColor: theme === 'dark' ? '#374151' : '#ffffff',
        borderWidth: 2,
      },
    ],
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: theme === 'dark' ? '#e5e7eb' : '#374151',
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.label}: R$ ${context.parsed.toFixed(2)}`;
          }
        }
      }
    }
  };

  if (currentView === 'profile') {
    return <Profile onBack={() => setCurrentView('dashboard')} />;
  }

  if (currentView === 'users') {
    return <UserManagement onBack={() => setCurrentView('dashboard')} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">💰</span>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Finanças Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200"
              >
                {theme === 'light' ? '🌙' : '☀️'}
              </button>
              <button
                onClick={() => setCurrentView('profile')}
                className="text-sm text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300"
              >
                👤 Perfil
              </button>
              {user?.role === 'admin' && (
                <button
                  onClick={() => setCurrentView('users')}
                  className="text-sm text-blue-600 dark:text-purple-400 hover:text-blue-800 dark:hover:text-purple-300"
                >
                  👥 Usuários
                </button>
              )}
              <span className="text-sm text-gray-600 dark:text-gray-300">Olá, {user?.name}</span>
              <button
                onClick={logout}
                className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow transition-colors duration-300">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <span className="text-2xl">📈</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">Receitas</p>
                  <p className="text-2xl font-semibold text-green-600 dark:text-green-400">
                    R$ {summary.total_income.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow transition-colors duration-300">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                  <span className="text-2xl">📉</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">Despesas</p>
                  <p className="text-2xl font-semibold text-red-600 dark:text-red-400">
                    R$ {summary.total_expense.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow transition-colors duration-300">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 dark:bg-purple-900/30 rounded-lg">
                  <span className="text-2xl">💰</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">Saldo</p>
                  <p className={`text-2xl font-semibold ${summary.balance >= 0 ? 'text-blue-600 dark:text-purple-400' : 'text-red-600 dark:text-red-400'}`}>
                    R$ {summary.balance.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow transition-colors duration-300">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <span className="text-2xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">Transações</p>
                  <p className="text-2xl font-semibold text-purple-600 dark:text-purple-400">
                    {summary.transactions_count}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Transactions List */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow transition-colors duration-300">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Transações Recentes</h2>
                <button
                  onClick={() => setShowForm(!showForm)}
                  className="bg-blue-600 dark:bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-purple-700 transition duration-200"
                >
                  + Nova Transação
                </button>
              </div>

              {showForm && (
                <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                  <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="Descrição"
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    />
                    <input
                      type="number"
                      placeholder="Valor"
                      step="0.01"
                      value={formData.amount}
                      onChange={(e) => setFormData({...formData, amount: e.target.value})}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    />
                    <select
                      value={formData.type}
                      onChange={(e) => setFormData({...formData, type: e.target.value, category_id: ''})}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="expense">Despesa</option>
                      <option value="income">Receita</option>
                    </select>
                    <select
                      value={formData.category_id}
                      onChange={(e) => setFormData({...formData, category_id: e.target.value})}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    >
                      <option value="">Selecione categoria</option>
                      {filteredCategories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                      ))}
                    </select>
                    <input
                      type="date"
                      value={formData.date}
                      onChange={(e) => setFormData({...formData, date: e.target.value})}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    />
                    <div className="flex space-x-2">
                      <button
                        type="submit"
                        className="bg-green-600 dark:bg-green-700 text-white px-4 py-2 rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition duration-200"
                      >
                        Salvar
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowForm(false)}
                        className="bg-gray-500 dark:bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-600 dark:hover:bg-gray-700 transition duration-200"
                      >
                        Cancelar
                      </button>
                    </div>
                  </form>
                </div>
              )}

              <div className="p-6">
                {transactions.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400 text-center py-8">Nenhuma transação ainda. Crie sua primeira transação!</p>
                ) : (
                  <div className="space-y-3">
                    {transactions.slice(0, 10).map(transaction => {
                      const category = categories.find(cat => cat.id === transaction.category_id);
                      return (
                        <div key={transaction.id} className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors duration-200">
                          <div className="flex items-center space-x-3">
                            <span className="text-2xl">
                              {transaction.type === 'income' ? '📈' : '📉'}
                            </span>
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">{transaction.description}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{category?.name} • {transaction.date}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className={`font-semibold ${transaction.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                              {transaction.type === 'income' ? '+' : '-'} R$ {transaction.amount.toFixed(2)}
                            </span>
                            <button
                              onClick={() => deleteTransaction(transaction.id)}
                              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Pie Chart */}
            {categorySummary.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 transition-colors duration-300">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Gastos por Categoria</h3>
                <div style={{ height: '300px' }}>
                  <Pie data={pieChartData} options={pieChartOptions} />
                </div>
              </div>
            )}

            {/* Categories Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow transition-colors duration-300">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Resumo por Categoria</h2>
              </div>
              <div className="p-6">
                {categorySummary.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400 text-center py-8">Nenhum dado ainda.</p>
                ) : (
                  <div className="space-y-4">
                    {categorySummary.map((cat, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div 
                            className="w-4 h-4 rounded-full" 
                            style={{ backgroundColor: cat.category_color }}
                          ></div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">{cat.category_name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{cat.transaction_count} transações</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-gray-900 dark:text-white">R$ {cat.total_amount.toFixed(2)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const { user, loading } = useAuth();
  const { theme } = useTheme();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center transition-colors duration-300">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 dark:border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Carregando...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <Login />;
};

// App with Providers
export default function AppWithProvider() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  );
}