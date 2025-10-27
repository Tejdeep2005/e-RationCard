import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { CreditCard, LogOut, Upload, Edit, CheckCircle, XCircle, Clock } from 'lucide-react';

const UserDashboard = ({ user, onLogout }) => {
  const [rationCard, setRationCard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showApply, setShowApply] = useState(false);
  const [showUpdate, setShowUpdate] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    family_members: 1,
    aadhaar: '',
    income_proof: '',
    photo: ''
  });

  useEffect(() => {
    fetchRationCard();
  }, []);

  const fetchRationCard = async () => {
    try {
      const response = await axios.get(`${API}/ration-cards/my-card`);
      setRationCard(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        setRationCard(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileUpload = async (e, field) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, [field]: reader.result });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleApply = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/ration-cards/apply`, formData);
      toast.success('Application submitted successfully!');
      setShowApply(false);
      fetchRationCard();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Application failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.put(`${API}/ration-cards/update`, formData);
      toast.success('Ration card updated successfully!');
      setShowUpdate(false);
      fetchRationCard();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: { variant: 'secondary', icon: <Clock className="w-4 h-4" />, text: 'Pending' },
      approved: { variant: 'default', icon: <CheckCircle className="w-4 h-4" />, text: 'Approved' },
      rejected: { variant: 'destructive', icon: <XCircle className="w-4 h-4" />, text: 'Rejected' },
      fake: { variant: 'destructive', icon: <XCircle className="w-4 h-4" />, text: 'Blocked - Fake' }
    };
    const config = variants[status] || variants.pending;
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        {config.icon}
        {config.text}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <div className="container mx-auto px-4 py-8" data-testid="user-dashboard">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 bg-white/10 backdrop-blur-lg p-6 rounded-2xl border border-white/20">
          <div>
            <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Welcome, {user.name}</h1>
            <p className="text-white/80">Manage your ration card</p>
          </div>
          <Button variant="secondary" onClick={onLogout} data-testid="logout-btn">
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Main Content */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-white"></div>
          </div>
        ) : rationCard ? (
          <Card className="backdrop-blur-xl bg-white/95 shadow-2xl border-0" data-testid="ration-card-display">
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-2xl">Your Ration Card</CardTitle>
                  <CardDescription>Card Status: {getStatusBadge(rationCard.status)}</CardDescription>
                </div>
                {(rationCard.status === 'approved' || rationCard.status === 'pending') && (
                  <Dialog open={showUpdate} onOpenChange={setShowUpdate}>
                    <DialogTrigger asChild>
                      <Button data-testid="update-card-btn">
                        <Edit className="w-4 h-4 mr-2" />
                        Update Details
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Update Ration Card</DialogTitle>
                        <DialogDescription>Update your ration card information</DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleUpdate} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="update-name">Full Name</Label>
                          <Input id="update-name" name="name" value={formData.name} onChange={handleChange} data-testid="update-name-input" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="update-address">Address</Label>
                          <Input id="update-address" name="address" value={formData.address} onChange={handleChange} data-testid="update-address-input" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="update-family">Family Members</Label>
                          <Input id="update-family" name="family_members" type="number" min="1" value={formData.family_members} onChange={handleChange} data-testid="update-family-input" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="update-aadhaar">Aadhaar Number</Label>
                          <Input id="update-aadhaar" name="aadhaar" value={formData.aadhaar} onChange={handleChange} data-testid="update-aadhaar-input" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="update-income">Income Proof (Upload)</Label>
                          <Input id="update-income" type="file" accept="image/*,.pdf" onChange={(e) => handleFileUpload(e, 'income_proof')} data-testid="update-income-input" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="update-photo">Photo (Upload)</Label>
                          <Input id="update-photo" type="file" accept="image/*" onChange={(e) => handleFileUpload(e, 'photo')} data-testid="update-photo-input" />
                        </div>
                        <Button type="submit" className="w-full" disabled={loading} data-testid="update-submit-btn">
                          {loading ? 'Updating...' : 'Update Card'}
                        </Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {rationCard.card_number && (
                <div className="bg-gradient-to-r from-purple-500 to-blue-500 p-6 rounded-xl text-white" data-testid="card-number-display">
                  <p className="text-sm opacity-80">Card Number</p>
                  <p className="text-3xl font-bold">{rationCard.card_number}</p>
                </div>
              )}
              <div className="grid md:grid-cols-2 gap-4">
                <div data-testid="card-name-display">
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-semibold">{rationCard.name}</p>
                </div>
                <div data-testid="card-family-display">
                  <p className="text-sm text-gray-500">Family Members</p>
                  <p className="font-semibold">{rationCard.family_members}</p>
                </div>
                <div data-testid="card-aadhaar-display">
                  <p className="text-sm text-gray-500">Aadhaar</p>
                  <p className="font-semibold">{rationCard.aadhaar}</p>
                </div>
                <div data-testid="card-status-display">
                  <p className="text-sm text-gray-500">Status</p>
                  <p className="font-semibold">{rationCard.status.toUpperCase()}</p>
                </div>
              </div>
              <div data-testid="card-address-display">
                <p className="text-sm text-gray-500">Address</p>
                <p className="font-semibold">{rationCard.address}</p>
              </div>
              {rationCard.ai_verification_result && (
                <div className="bg-blue-50 p-4 rounded-lg" data-testid="ai-verification-display">
                  <p className="text-sm font-semibold text-blue-800 mb-1">AI Verification Result</p>
                  <p className="text-sm text-blue-700">{rationCard.ai_verification_result}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card className="backdrop-blur-xl bg-white/95 shadow-2xl border-0" data-testid="no-card-display">
            <CardContent className="text-center py-16">
              <CreditCard className="w-24 h-24 mx-auto text-gray-300 mb-6" />
              <h3 className="text-2xl font-bold mb-2">No Ration Card Found</h3>
              <p className="text-gray-600 mb-6">You haven't applied for a ration card yet</p>
              <Dialog open={showApply} onOpenChange={setShowApply}>
                <DialogTrigger asChild>
                  <Button size="lg" data-testid="apply-now-btn">
                    <Upload className="w-4 h-4 mr-2" />
                    Apply Now
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Apply for Ration Card</DialogTitle>
                    <DialogDescription>Fill in your details to apply</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleApply} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="apply-name">Full Name *</Label>
                      <Input id="apply-name" name="name" value={formData.name} onChange={handleChange} required data-testid="apply-name-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apply-address">Address *</Label>
                      <Input id="apply-address" name="address" value={formData.address} onChange={handleChange} required data-testid="apply-address-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apply-family">Family Members *</Label>
                      <Input id="apply-family" name="family_members" type="number" min="1" value={formData.family_members} onChange={handleChange} required data-testid="apply-family-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apply-aadhaar">Aadhaar Number (12 digits) *</Label>
                      <Input id="apply-aadhaar" name="aadhaar" value={formData.aadhaar} onChange={handleChange} pattern="[0-9]{12}" required data-testid="apply-aadhaar-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apply-income">Income Proof (Upload) *</Label>
                      <Input id="apply-income" type="file" accept="image/*,.pdf" onChange={(e) => handleFileUpload(e, 'income_proof')} required data-testid="apply-income-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apply-photo">Photo (Upload) *</Label>
                      <Input id="apply-photo" type="file" accept="image/*" onChange={(e) => handleFileUpload(e, 'photo')} required data-testid="apply-photo-input" />
                    </div>
                    <Button type="submit" className="w-full" disabled={loading} data-testid="apply-submit-btn">
                      {loading ? 'Submitting...' : 'Submit Application'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default UserDashboard;